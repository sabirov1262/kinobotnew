from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import settings
from database import Database
from handlers import admin, movies, subscription, user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, db: Database) -> None:
    settings.validate()
    await db.connect()
    await db.init()
    await bot.set_webhook(settings.webhook_url)
    logger.info("Webhook o‘rnatildi: %s", settings.webhook_url)


async def on_shutdown(bot: Bot, db: Database) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await db.close()
    await bot.session.close()
    logger.info("Bot to‘xtatildi.")


async def healthcheck(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app() -> web.Application:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    db = Database(settings.database_url)

    dp["db"] = db
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(subscription.router)
    dp.include_router(movies.router)

    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/healthz", healthcheck)

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    async def startup(_: web.Application) -> None:
        await on_startup(bot, db)

    async def shutdown(_: web.Application) -> None:
        await on_shutdown(bot, db)

    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)
    return app


def main() -> None:
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=settings.port)


if __name__ == "__main__":
    main()
