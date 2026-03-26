from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards import back_only_kb, subscription_menu_kb, admin_panel_kb
from states import SubscriptionState
from utils.validators import classify_subscription_value

router = Router()


def admin_only(message: Message) -> bool:
    return message.from_user.id == settings.super_admin_id


@router.message(F.text == "📣 Telegram kanal / guruh")
async def ask_telegram_link(message: Message, state: FSMContext):
    if not admin_only(message):
        return
    await state.set_state(SubscriptionState.waiting_telegram_link)
    await message.answer(
        "📣 Kanal / Guruh ma’lumotini yuboring\n\n"
        "Qabul qilinadigan formatlar:\n"
        "• @username\n"
        "• -1001234567890\n"
        "• https://t.me/username\n"
        "• https://t.me/+invitecode",
        reply_markup=back_only_kb(),
    )


@router.message(F.text == "🔗 Shaxsiy / so‘rovli havola")
async def ask_private_link(message: Message, state: FSMContext):
    if not admin_only(message):
        return
    await state.set_state(SubscriptionState.waiting_private_link)
    await message.answer(
        "🔗 Shaxsiy yoki so‘rovli havolani yuboring.\n\n"
        "Masalan: https://t.me/+abc123xyz",
        reply_markup=back_only_kb(),
    )


@router.message(F.text == "🌐 Oddiy https havola")
async def ask_external_link(message: Message, state: FSMContext):
    if not admin_only(message):
        return
    await state.set_state(SubscriptionState.waiting_external_link)
    await message.answer(
        "🌐 Oddiy https havolani yuboring.\n\n"
        "Masalan:\n"
        "• https://instagram.com/...\n"
        "• https://youtube.com/...\n"
        "• https://youtu.be/...\n"
        "• https://example.com/...",
        reply_markup=back_only_kb(),
    )


async def _save_link(message: Message, state: FSMContext, db, expected_type: str) -> None:
    value = (message.text or "").strip()
    if value == "◀️ Orqaga":
        await state.clear()
        await message.answer("🔐 Majburiy obuna", reply_markup=subscription_menu_kb())
        return

    real_type = classify_subscription_value(value)
    if real_type is None:
        await message.answer("❌ Noto‘g‘ri format. Iltimos, to‘g‘ri havola yuboring.")
        return

    if expected_type == "telegram" and real_type not in {"telegram", "private"}:
        await message.answer("❌ Bu bo‘lim faqat Telegram ma’lumotlari uchun.")
        return
    if expected_type == "private" and real_type != "private":
        await message.answer("❌ Bu bo‘lim faqat t.me/+ private havolalar uchun.")
        return
    if expected_type == "external" and not value.startswith("https://"):
        await message.answer("❌ Havola https:// bilan boshlanishi kerak.")
        return

    store_type = expected_type if expected_type != "telegram" or real_type == "telegram" else "private"
    await db.add_subscription(store_type, value)
    await state.clear()
    await message.answer("✅ Havola saqlandi.", reply_markup=subscription_menu_kb())


@router.message(SubscriptionState.waiting_telegram_link)
async def save_telegram_link(message: Message, state: FSMContext, db):
    await _save_link(message, state, db, "telegram")


@router.message(SubscriptionState.waiting_private_link)
async def save_private_link(message: Message, state: FSMContext, db):
    await _save_link(message, state, db, "private")


@router.message(SubscriptionState.waiting_external_link)
async def save_external_link(message: Message, state: FSMContext, db):
    await _save_link(message, state, db, "external")


@router.message(F.text == "📋 Ulangan linklar")
async def list_links(message: Message, db):
    if not admin_only(message):
        return
    items = await db.list_subscriptions()
    if not items:
        await message.answer("📋 Hozircha ulangan linklar yo‘q.", reply_markup=subscription_menu_kb())
        return

    lines = ["📋 Ulangan linklar:\n"]
    for item in items:
        icon = {"telegram": "📣", "private": "🔗", "external": "🌐"}.get(item["link_type"], "🔗")
        lines.append(f"{icon} ID {item['id']} — {item['value']}")
    await message.answer("\n".join(lines), reply_markup=subscription_menu_kb())


@router.message(F.text == "🗑 O‘chirish")
async def ask_delete_link(message: Message, state: FSMContext):
    if not admin_only(message):
        return
    await state.set_state(SubscriptionState.waiting_delete_link_id)
    await message.answer("🗑 O‘chirish uchun link ID raqamini yuboring.", reply_markup=back_only_kb())


@router.message(SubscriptionState.waiting_delete_link_id)
async def delete_link(message: Message, state: FSMContext, db):
    raw = (message.text or "").strip()
    if raw == "◀️ Orqaga":
        await state.clear()
        await message.answer("🔐 Majburiy obuna", reply_markup=subscription_menu_kb())
        return

    if not raw.isdigit():
        await message.answer("❌ Faqat ID raqamini yuboring.")
        return

    result = await db.delete_subscription(int(raw))
    await state.clear()
    if result.endswith("DELETE 1"):
        await message.answer("✅ Havola o‘chirildi.", reply_markup=subscription_menu_kb())
    else:
        await message.answer("❌ Bunday ID topilmadi.", reply_markup=subscription_menu_kb())


@router.message(F.text == "🔒 Saqlashni taqiqlash")
async def enable_protect(message: Message, db):
    if not admin_only(message):
        return
    await db.set_setting("protect_content", "1")
    await message.answer("🔒 Endi kinolar protect_content bilan yuboriladi.", reply_markup=admin_panel_kb())


@router.message(F.text == "🔓 Saqlashga ruxsat berish")
async def disable_protect(message: Message, db):
    if not admin_only(message):
        return
    await db.set_setting("protect_content", "0")
    await message.answer("🔓 Endi kinolarni oddiy yuborish yoqildi.", reply_markup=admin_panel_kb())
