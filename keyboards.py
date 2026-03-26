from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🎬 Kino olish")],
    ]
    if is_admin:
        rows.extend([
            [KeyboardButton(text="🎛 Admin panel")],
        ])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_panel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kinolar"), KeyboardButton(text="🔐 Majburiy obuna")],
            [KeyboardButton(text="🔒 Kontent himoyasi"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🔒 Saqlashni taqiqlash"), KeyboardButton(text="🔓 Saqlashga ruxsat berish")],
            [KeyboardButton(text="🏠 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def movies_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Kino yuklash"), KeyboardButton(text="🔍 Kod bo‘yicha qidirish")],
            [KeyboardButton(text="🗑 Kino o‘chirish"), KeyboardButton(text="📚 Kinolar ro‘yxati")],
            [KeyboardButton(text="◀️ Orqaga")],
        ],
        resize_keyboard=True,
    )


def subscription_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📣 Telegram kanal / guruh")],
            [KeyboardButton(text="🔗 Shaxsiy / so‘rovli havola")],
            [KeyboardButton(text="🌐 Oddiy https havola")],
            [KeyboardButton(text="📋 Ulangan linklar"), KeyboardButton(text="🗑 O‘chirish")],
            [KeyboardButton(text="◀️ Orqaga")],
        ],
        resize_keyboard=True,
    )


def back_only_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="◀️ Orqaga")]], resize_keyboard=True)


def force_subscribe_check_kb(items: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        label = {
            "telegram": "📣 Ochish",
            "private": "🔗 Ochish",
            "external": "🌐 Ochish",
        }.get(item["link_type"], "🔗 Ochish")
        buttons.append([InlineKeyboardButton(text=f"{label} #{item['id']}", url=item["value"])])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_force_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
