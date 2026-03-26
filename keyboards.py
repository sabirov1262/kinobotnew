from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_admin_keyboard():
    keyboard = [
        [KeyboardButton("📊 Statistika"), KeyboardButton("📨 Xabar yuborish")],
        [KeyboardButton("🎬 Kinolar"), KeyboardButton("🔐 Kanallar")],
        [KeyboardButton("👮 Adminlar"), KeyboardButton("⚙️ Sozlamalar")],
        [KeyboardButton("◀️ Orqaga")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def main_user_keyboard():
    keyboard = [
        [KeyboardButton("🎬 Kinolar")],
        [KeyboardButton("⭐ Premium")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_panel_inline():
    keyboard = [
        [
            InlineKeyboardButton("📊 Statistika", callback_data="stat"),
            InlineKeyboardButton("📨 Xabar yuborish", callback_data="broadcast"),
        ],
        [
            InlineKeyboardButton("🎬 Kinolar", callback_data="movies"),
            InlineKeyboardButton("🔐 Kanallar", callback_data="channels"),
        ],
        [
            InlineKeyboardButton("👮 Adminlar", callback_data="admins"),
            InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def movies_keyboard():
    keyboard = [
        [InlineKeyboardButton("📥 Kino yuklash", callback_data="movie_add")],
        [
            InlineKeyboardButton("✏️ Kino tahrirlash", callback_data="movie_edit"),
            InlineKeyboardButton("🗑 Kino o'chirish", callback_data="movie_delete"),
        ],
        [InlineKeyboardButton("📋 Kinolar ro'yxati", callback_data="movie_list")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def channels_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="ch_add")],
        [InlineKeyboardButton("📋 Ro'yxatni ko'rish", callback_data="ch_list")],
        [InlineKeyboardButton("🗑 Kanalni o'chirish", callback_data="ch_delete")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def channel_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Ommaviy / Shaxsiy (Kanal · Guruh)", callback_data="chtype_public")],
        [InlineKeyboardButton("🔐 Shaxsiy / So'rovli havola", callback_data="chtype_private")],
        [InlineKeyboardButton("🌐 Oddiy havola", callback_data="chtype_link")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="channels")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admins_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("➕ Admin qo'shish", callback_data="admin_add"),
            InlineKeyboardButton("➖ Adminni o'chirish", callback_data="admin_remove"),
        ],
        [InlineKeyboardButton("📋 Adminlar ro'yxati", callback_data="admin_list")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def settings_keyboard(sharing_on=True):
    share_text = f"↗️ Ulashish ({'🔒 Ruxsat etilgan' if sharing_on else '🔓 Taqiqlangan'})"
    keyboard = [
        [InlineKeyboardButton(share_text, callback_data="toggle_sharing")],
        [
            InlineKeyboardButton("💳 To'lov tizimlar", callback_data="payment_settings"),
            InlineKeyboardButton("⚙️ Premium", callback_data="premium_settings"),
        ],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def premium_settings_keyboard():
    keyboard = [
        [InlineKeyboardButton("💡 Holat o'zgartirish", callback_data="toggle_premium")],
        [InlineKeyboardButton("👥 Premium foydalanuvchilar ro'yxati", callback_data="premium_users")],
        [InlineKeyboardButton("📋 Premium tariflar", callback_data="premium_tariffs")],
        [InlineKeyboardButton("➕ Premium berish / Muddatni boshqarish", callback_data="give_premium")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def payment_settings_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚡ Avtomatik to'lov tizimlari", callback_data="auto_payment")],
        [InlineKeyboardButton("📝 Oddiy to'lov tizimlari", callback_data="manual_payment")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def broadcast_type_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("💬 Oddiy", callback_data="broadcast_normal"),
            InlineKeyboardButton("📨 Forward", callback_data="broadcast_forward"),
        ],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def tariff_list_keyboard(tariffs):
    keyboard = []
    for t in tariffs:
        keyboard.append([
            InlineKeyboardButton(
                f"{'🟢' if t['is_active'] else '🔴'} {t['name']} - {t['price']:,} so'm",
                callback_data=f"tariff_{t['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("➕ Tarif qo'shish", callback_data="tariff_add")])
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="premium_settings")])
    return InlineKeyboardMarkup(keyboard)


def tariff_manage_keyboard(tariff_id):
    keyboard = [
        [InlineKeyboardButton("✏️ Nomni o'zgartirish", callback_data=f"tariff_edit_name_{tariff_id}")],
        [InlineKeyboardButton("📅 Muddatni o'zgartirish", callback_data=f"tariff_edit_days_{tariff_id}")],
        [InlineKeyboardButton("💰 Narxni o'zgartirish", callback_data=f"tariff_edit_price_{tariff_id}")],
        [InlineKeyboardButton("🔄 Holatni o'zgartirish", callback_data=f"tariff_toggle_{tariff_id}")],
        [InlineKeyboardButton("🗑 O'chirish", callback_data=f"tariff_del_{tariff_id}")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="premium_tariffs")],
    ]
    return InlineKeyboardMarkup(keyboard)


def movie_list_keyboard(movies):
    keyboard = []
    for m in movies:
        keyboard.append([
            InlineKeyboardButton(
                f"🎬 [{m['code']}] {m['title'][:30]}",
                callback_data=f"mv_{m['code']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="movies")])
    return InlineKeyboardMarkup(keyboard)


def movie_manage_keyboard(code):
    keyboard = [
        [InlineKeyboardButton("✏️ Nomni o'zgartirish", callback_data=f"mv_edit_title_{code}")],
        [InlineKeyboardButton("📝 Tavsifni o'zgartirish", callback_data=f"mv_edit_caption_{code}")],
        [InlineKeyboardButton("🗑 O'chirish", callback_data=f"mv_del_{code}")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="movie_list")],
    ]
    return InlineKeyboardMarkup(keyboard)


def channels_list_keyboard(channels):
    keyboard = []
    for ch in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"⚙️ {ch['channel_name'] or ch['channel_id']}",
                callback_data=f"ch_{ch['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="channels")])
    return InlineKeyboardMarkup(keyboard)


def subscribe_keyboard(channels):
    keyboard = []
    for ch in channels:
        link = ch['channel_link'] or f"https://t.me/{ch['channel_id'].lstrip('@')}"
        keyboard.append([
            InlineKeyboardButton(
                f"📢 {ch['channel_name'] or ch['channel_id']}",
                url=link
            )
        ])
    keyboard.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(keyboard)


def back_keyboard(target="admin_back"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Orqaga", callback_data=target)]])


def confirm_keyboard(yes_data, no_data="admin_back"):
    keyboard = [
        [
            InlineKeyboardButton("✅ Ha", callback_data=yes_data),
            InlineKeyboardButton("❌ Yo'q", callback_data=no_data),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
