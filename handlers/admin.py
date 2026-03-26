from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message

from config import settings
from keyboards import admin_panel_kb, movies_menu_kb, subscription_menu_kb

router = Router()


def admin_only(message: Message) -> bool:
    return message.from_user.id == settings.super_admin_id


@router.message(F.text == "🎬 Kinolar")
async def movies_section(message: Message):
    if not admin_only(message):
        return
    await message.answer(
        "🎬 Kinolar bo‘limi\n\n"
        "Bu yerda kino yuklash, kod bo‘yicha qidirish, o‘chirish va ro‘yxatni ko‘rish mumkin.",
        reply_markup=movies_menu_kb(),
    )


@router.message(F.text == "🔐 Majburiy obuna")
async def subscriptions_section(message: Message):
    if not admin_only(message):
        return
    await message.answer(
        "🔐 Majburiy obuna turini tanlang\n\n"
        "Quyida majburiy obunani qo‘shishning 3 ta turi mavjud.\n"
        "Siz Telegram kanal/guruh, shaxsiy taklif havolasi yoki oddiy tashqi https havolalarni ulashingiz mumkin.",
        reply_markup=subscription_menu_kb(),
    )


@router.message(F.text == "🔒 Kontent himoyasi")
async def content_protection_section(message: Message, db):
    if not admin_only(message):
        return
    enabled = await db.get_setting("protect_content", "0")
    status = "🔒 Yoqilgan" if enabled == "1" else "🔓 O‘chiq"
    await message.answer(
        "🛡 Kontent himoyasi\n\n"
        f"Hozirgi holat: {status}\n\n"
        "Bu sozlama yoqilsa, bot yuborayotgan kinolar protect_content bilan jo‘natiladi.",
        reply_markup=admin_panel_kb(),
    )


@router.message(F.text == "📊 Statistika")
async def stats(message: Message, db):
    if not admin_only(message):
        return
    data = await db.get_stats()
    await message.answer(
        "📊 Bot statistikasi\n\n"
        f"👤 Foydalanuvchilar: {data['users']}\n"
        f"🎬 Kinolar: {data['movies']}\n"
        f"🔗 Ulangan linklar: {data['links']}",
        reply_markup=admin_panel_kb(),
    )


@router.message(F.text == "◀️ Orqaga")
async def back_from_submenus(message: Message):
    if not admin_only(message):
        return
    await message.answer("🎛 Admin panel", reply_markup=admin_panel_kb())
