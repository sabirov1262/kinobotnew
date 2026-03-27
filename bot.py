import logging
import os

from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN
from database import init_db
from handlers import start_handler, button_handler, message_handler

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
    return app


async def healthcheck(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def telegram_webhook(request: web.Request) -> web.Response:
    ptb_app: Application = request.app["ptb_app"]

    try:
        data = await request.json()
        logger.info("📩 Update keldi: %s", data)

        update = Update.de_json(data, ptb_app.bot)
        await ptb_app.process_update(update)

        return web.Response(text="OK")
    except Exception as e:
        logger.exception("❌ Webhook update ishlashda xato: %s", e)
        return web.Response(text="ERROR", status=500)


async def on_startup(app_web: web.Application) -> None:
    ptb_app: Application = app_web["ptb_app"]

    logger.info("🚀 Startup boshlandi")
    await init_db()
    logger.info("✅ Database tayyor!")

    await ptb_app.initialize()
    await ptb_app.start()

    await ptb_app.bot.delete_webhook(drop_pending_updates=True)
    await ptb_app.bot.set_webhook(WEBHOOK_URL)

    logger.info("✅ Webhook o‘rnatildi: %s", WEBHOOK_URL)
    logger.info("✅ Server portda ishga tushdi: %s", PORT)


async def on_shutdown(app_web: web.Application) -> None:
    ptb_app: Application = app_web["ptb_app"]

    try:
        await ptb_app.bot.delete_webhook()
    except Exception as e:
        logger.warning("Webhook o‘chirishda xato: %s", e)

    await ptb_app.stop()
    await ptb_app.shutdown()
    logger.info("🛑 Bot to‘xtatildi")


def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("BOT_TOKEN environment variable topilmadi")

    if not WEBHOOK_HOST:
        raise RuntimeError("WEBHOOK_HOST environment variable topilmadi")

    ptb_app = build_app()

    app_web = web.Application()
    app_web["ptb_app"] = ptb_app

    app_web.router.add_get("/", healthcheck)
    app_web.router.add_post(WEBHOOK_PATH, telegram_webhook)

    app_web.on_startup.append(on_startup)
    app_web.on_shutdown.append(on_shutdown)

    logger.info("🌐 Web server ishga tushmoqda...")
    web.run_app(app_web, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
