from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import (
    get_user, add_user, is_admin, get_setting,
    get_channels, get_movie, increment_views, is_premium_user
)
from keyboards import main_admin_keyboard, subscribe_keyboard
from states import get_state, clear_state, IDLE
import states as st
import admin_handlers as adm
import movie_handlers as mv_h
import channel_handlers as ch_h
import tariff_handlers as tr_h
import broadcast_handlers as bc_h
from config import SUPER_ADMIN_ID


async def admin_check(user_id: int) -> bool:
    return await is_admin(user_id)


async def check_subscription(bot, user_id: int, channels: list) -> list:
    """Foydalanuvchi obuna bo'lmagan kanallarni qaytaradi"""
    not_subscribed = []
    for ch in channels:
        ch_type = ch['channel_type']
        if ch_type == 'link':
            continue  # Link tipidagi kanallarni tekshirib bo'lmaydi
        try:
            channel_id = ch['channel_id']
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status in ['left', 'kicked', 'banned']:
                not_subscribed.append(ch)
        except TelegramError:
            not_subscribed.append(ch)
    return not_subscribed


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await add_user(user.id, user.username or "", user.full_name or "")
    clear_state(user.id)

    # Deep link tekshirish (kino kodi)
    args = context.args
    if args:
        code = args[0]
        await send_movie(update, context, code)
        return

    welcome = await get_setting('welcome_message')
    welcome = welcome.format(name=user.first_name) if welcome else \
        f"👋 Assalomu alaykum {user.first_name} botimizga xush kelibsiz.\n\n🤝 Kino kodini yuboring..."

    is_adm = await admin_check(user.id)
    keyboard = main_admin_keyboard() if is_adm else None

    await update.message.reply_text(welcome, reply_markup=keyboard)


async def send_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    user = update.effective_user

    # Obuna tekshirish
    sub_required = await get_setting('subscription_required')
    if sub_required == '1':
        channels = await get_channels()
        if channels:
            not_sub = await check_subscription(context.bot, user.id, channels)
            if not_sub:
                kb = subscribe_keyboard(not_sub)
                await update.message.reply_text(
                    "⚠️ Kinoni ko'rish uchun quyidagi kanallarga obuna bo'ling:",
                    reply_markup=kb
                )
                return

    movie = await get_movie(code)
    if not movie:
        await update.message.reply_text("❌ Bunday kodli kino topilmadi!")
        return

    await increment_views(code)
    caption = movie['caption'] or movie['title']

    try:
        ftype = movie['file_type']
        if ftype == 'video':
            await update.message.reply_video(
                movie['file_id'], caption=caption
            )
        elif ftype == 'document':
            await update.message.reply_document(
                movie['file_id'], caption=caption
            )
        elif ftype == 'photo':
            await update.message.reply_photo(
                movie['file_id'], caption=caption
            )
        else:
            await update.message.reply_video(movie['file_id'], caption=caption)
    except TelegramError as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    text = update.message.text or ""

    # State tekshirish
    state_info = get_state(user.id)
    state = state_info["state"]

    # Admin tugmalari
    is_adm = await admin_check(user.id)

    if text == "📊 Statistika" and is_adm:
        await adm.show_statistics(update, context)
        return
    elif text == "📨 Xabar yuborish" and is_adm:
        await bc_h.start_broadcast(update, context)
        return
    elif text == "🎬 Kinolar" and is_adm:
        await mv_h.movies_menu(update, context)
        return
    elif text == "🔐 Kanallar" and is_adm:
        await ch_h.channels_menu(update, context)
        return
    elif text == "👮 Adminlar" and is_adm:
        await adm.admins_menu(update, context)
        return
    elif text == "⚙️ Sozlamalar" and is_adm:
        await adm.settings_menu(update, context)
        return
    elif text == "◀️ Orqaga" and is_adm:
        clear_state(user.id)
        await update.message.reply_text(
            "Admin paneliga xush kelibsiz!",
            reply_markup=main_admin_keyboard()
        )
        return

    # State bo'yicha routing
    if state == st.WAITING_MOVIE_FILE:
        await mv_h.handle_movie_file(update, context)
        return
    elif state == st.WAITING_MOVIE_CODE:
        await mv_h.handle_movie_code(update, context)
        return
    elif state == st.WAITING_MOVIE_TITLE:
        await mv_h.handle_movie_title(update, context)
        return
    elif state == st.WAITING_MOVIE_CAPTION:
        await mv_h.handle_movie_caption(update, context)
        return
    elif state == st.WAITING_MOVIE_EDIT_CODE:
        await mv_h.handle_edit_code(update, context)
        return
    elif state == st.WAITING_MOVIE_EDIT_VALUE:
        await mv_h.handle_edit_value(update, context)
        return
    elif state == st.WAITING_MOVIE_DELETE_CODE:
        await mv_h.handle_delete_code(update, context)
        return
    elif state == st.WAITING_CHANNEL_ID:
        await ch_h.handle_channel_id(update, context)
        return
    elif state == st.WAITING_CHANNEL_NAME:
        await ch_h.handle_channel_name(update, context)
        return
    elif state == st.WAITING_CHANNEL_LINK:
        await ch_h.handle_channel_link(update, context)
        return
    elif state == st.WAITING_ADMIN_ID:
        await adm.handle_add_admin(update, context)
        return
    elif state == st.WAITING_ADMIN_REMOVE_ID:
        await adm.handle_remove_admin(update, context)
        return
    elif state == st.WAITING_BROADCAST_MSG:
        await bc_h.handle_broadcast_message(update, context)
        return
    elif state == st.WAITING_TARIFF_NAME:
        await tr_h.handle_tariff_name(update, context)
        return
    elif state == st.WAITING_TARIFF_DAYS:
        await tr_h.handle_tariff_days(update, context)
        return
    elif state == st.WAITING_TARIFF_PRICE:
        await tr_h.handle_tariff_price(update, context)
        return
    elif state == st.WAITING_TARIFF_EDIT_VALUE:
        await tr_h.handle_tariff_edit_value(update, context)
        return
    elif state == st.WAITING_GIVE_PREMIUM_ID:
        await adm.handle_give_premium_id(update, context)
        return
    elif state == st.WAITING_GIVE_PREMIUM_DAYS:
        await adm.handle_give_premium_days(update, context)
        return

    # Kino kodi qidiruvi (faqat raqam yoki qisqa kod)
    if text and not text.startswith('/'):
        await send_movie(update, context, text.strip())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user
    is_adm = await admin_check(user.id)

    if data == "check_sub":
        channels = await get_channels()
        not_sub = await check_subscription(context.bot, user.id, channels)
        if not_sub:
            kb = subscribe_keyboard(not_sub)
            await query.edit_message_text(
                "⚠️ Hali ham obuna bo'lmagansiz!\n\nQuyidagi kanallarga obuna bo'ling:",
                reply_markup=kb
            )
        else:
            await query.edit_message_text("✅ Rahmat! Endi kino kodini yuboring.")
        return

    # Admin panel
    if not is_adm:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    if data == "admin_back" or data == "stat":
        await adm.show_statistics(update, context)
    elif data == "broadcast":
        await bc_h.start_broadcast(update, context)
    elif data == "broadcast_normal":
        await bc_h.set_broadcast_normal(update, context)
    elif data == "broadcast_forward":
        await bc_h.set_broadcast_forward(update, context)
    elif data == "movies":
        await mv_h.movies_menu(update, context)
    elif data == "movie_add":
        await mv_h.start_add_movie(update, context)
    elif data == "movie_list":
        await mv_h.show_movie_list(update, context)
    elif data == "movie_edit":
        await mv_h.start_edit_movie(update, context)
    elif data == "movie_delete":
        await mv_h.start_delete_movie(update, context)
    elif data.startswith("mv_del_"):
        code = data.replace("mv_del_", "")
        await mv_h.confirm_delete_movie(update, context, code)
    elif data.startswith("mv_del_confirm_"):
        code = data.replace("mv_del_confirm_", "")
        await mv_h.do_delete_movie(update, context, code)
    elif data.startswith("mv_edit_title_"):
        code = data.replace("mv_edit_title_", "")
        await mv_h.edit_title(update, context, code)
    elif data.startswith("mv_edit_caption_"):
        code = data.replace("mv_edit_caption_", "")
        await mv_h.edit_caption(update, context, code)
    elif data.startswith("mv_"):
        code = data.replace("mv_", "")
        await mv_h.show_movie_detail(update, context, code)
    elif data == "channels":
        await ch_h.channels_menu(update, context)
    elif data == "ch_add":
        await ch_h.start_add_channel(update, context)
    elif data.startswith("chtype_"):
        ch_type = data.replace("chtype_", "")
        await ch_h.set_channel_type(update, context, ch_type)
    elif data == "ch_list":
        await ch_h.show_channel_list(update, context)
    elif data == "ch_delete":
        await ch_h.start_delete_channel(update, context)
    elif data.startswith("ch_del_confirm_"):
        ch_id = data.replace("ch_del_confirm_", "")
        await ch_h.do_delete_channel(update, context, ch_id)
    elif data.startswith("ch_"):
        ch_id = data.replace("ch_", "")
        await ch_h.show_channel_detail(update, context, ch_id)
    elif data == "admins":
        await adm.admins_menu(update, context)
    elif data == "admin_add":
        await adm.start_add_admin(update, context)
    elif data == "admin_remove":
        await adm.start_remove_admin(update, context)
    elif data == "admin_list":
        await adm.show_admin_list(update, context)
    elif data == "settings":
        await adm.settings_menu(update, context)
    elif data == "toggle_sharing":
        await adm.toggle_sharing(update, context)
    elif data == "payment_settings":
        await adm.payment_settings(update, context)
    elif data == "auto_payment":
        await query.edit_message_text(
            "⚡ Avtomatik to'lov tizimlari\n\n"
            "Hozircha qo'llab-quvvatlanmaydi. Tez orada qo'shiladi.",
            reply_markup=__import__('keyboards').back_keyboard("payment_settings")
        )
    elif data == "manual_payment":
        await query.edit_message_text(
            "📝 Oddiy to'lov tizimlari\n\n"
            "Foydalanuvchi to'lovni amalga oshirib, admin tasdiqlaydi.",
            reply_markup=__import__('keyboards').back_keyboard("payment_settings")
        )
    elif data == "premium_settings":
        await adm.premium_settings_menu(update, context)
    elif data == "toggle_premium":
        await adm.toggle_premium(update, context)
    elif data == "premium_users":
        await adm.show_premium_users(update, context)
    elif data == "premium_tariffs":
        await tr_h.show_tariffs(update, context)
    elif data == "tariff_add":
        await tr_h.start_add_tariff(update, context)
    elif data.startswith("tariff_edit_name_"):
        tid = int(data.replace("tariff_edit_name_", ""))
        await tr_h.edit_tariff_field(update, context, tid, "name")
    elif data.startswith("tariff_edit_days_"):
        tid = int(data.replace("tariff_edit_days_", ""))
        await tr_h.edit_tariff_field(update, context, tid, "duration_days")
    elif data.startswith("tariff_edit_price_"):
        tid = int(data.replace("tariff_edit_price_", ""))
        await tr_h.edit_tariff_field(update, context, tid, "price")
    elif data.startswith("tariff_toggle_"):
        tid = int(data.replace("tariff_toggle_", ""))
        await tr_h.toggle_tariff(update, context, tid)
    elif data.startswith("tariff_del_"):
        tid = int(data.replace("tariff_del_", ""))
        await tr_h.delete_tariff(update, context, tid)
    elif data.startswith("tariff_"):
        tid = int(data.replace("tariff_", ""))
        await tr_h.show_tariff_detail(update, context, tid)
    elif data == "give_premium":
        await adm.start_give_premium(update, context)
