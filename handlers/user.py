from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards import main_menu, admin_panel_kb, force_subscribe_check_kb
from utils.validators import TELEGRAM_USERNAME_RE, TELEGRAM_TME_RE

router = Router()
logger = logging.getLogger(__name__)


async def _check_one_telegram_requirement(bot, user_id: int, value: str) -> bool:
    try:
        if TELEGRAM_USERNAME_RE.match(value):
            chat = await bot.get_chat(value)
        elif TELEGRAM_TME_RE.match(value):
            chat_username = value.rstrip("/").split("/")[-1]
            if chat_username.startswith("+"):
                return True
            chat = await bot.get_chat("@" + chat_username)
        else:
            # Numeric IDs can’t be validated against public membership reliably for arbitrary channels.
            return True

        member = await bot.get_chat_member(chat.id, user_id)
        return member.status not in {"left", "kicked"}
    except Exception:
        return False


async def ensure_force_subscription(message: Message, bot, db) -> bool:
    enabled = await db.get_setting("force_subscriptions_enabled", "1")
    if enabled != "1":
        return True

    items = await db.list_subscriptions()
    if not items:
        return True

    pending = []
    for item in items:
        if item["link_type"] == "telegram":
            ok = await _check_one_telegram_requirement(bot, message.from_user.id, item["value"])
            if not ok:
                pending.append(item)
        else:
            pending.append(item)

    if pending:
        text = (
            "🔐 Botdan foydalanish uchun quyidagi manbalarni ko‘rib chiqing.\n\n"
            "Quyida siz uchun ulangan kanal, guruh va tashqi havolalar berilgan.\n"
            "Hammasini ochib bo‘lgach, pastdagi “✅ Tekshirish” tugmasini bosing."
        )
        await message.answer(text, reply_markup=force_subscribe_check_kb(pending))
        return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db):
    await state.clear()
    await db.upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    if not await ensure_force_subscription(message, message.bot, db):
        return

    is_admin = message.from_user.id == settings.super_admin_id
    text = (
        "🎬 Assalomu alaykum!\n\n"
        "Bu bot orqali kino kodini yuborib, kerakli kinoni olishingiz mumkin.\n"
        "Agar siz admin bo‘lsangiz, pastdagi menyudan boshqaruv paneliga ham kira olasiz."
    )
    await message.answer(text, reply_markup=main_menu(is_admin=is_admin))


@router.callback_query(F.data == "check_force_sub")
async def callback_check_force_sub(callback: CallbackQuery, db):
    fake_message = callback.message
    fake_message.from_user = callback.from_user  # type: ignore[attr-defined]
    if await ensure_force_subscription(fake_message, callback.bot, db):
        await callback.message.answer(
            "✅ Tekshiruv muvaffaqiyatli yakunlandi.",
            reply_markup=main_menu(is_admin=callback.from_user.id == settings.super_admin_id),
        )
        await callback.message.delete()
    else:
        await callback.answer("Hali barcha manbalar ochilmagan.", show_alert=True)


@router.message(F.text == "🎬 Kino olish")
async def movie_help(message: Message, db):
    if not await ensure_force_subscription(message, message.bot, db):
        return
    await message.answer(
        "🔎 Kino olish uchun kod yuboring.\n\n"
        "Masalan: 100, kino77 yoki avatar2",
    )


@router.message(F.text == "🎛 Admin panel")
async def admin_panel(message: Message):
    if message.from_user.id != settings.super_admin_id:
        await message.answer("❌ Sizda admin panelga kirish huquqi yo‘q.")
        return
    await message.answer(
        "🎛 Admin panel\n\nKerakli bo‘limni pastdagi tugmalar orqali tanlang.",
        reply_markup=admin_panel_kb(),
    )


@router.message(F.text == "🏠 Bosh menyu")
async def back_main(message: Message):
    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu(is_admin=message.from_user.id == settings.super_admin_id),
    )
