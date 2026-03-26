from telegram import Update
from telegram.ext import ContextTypes

from database import add_channel, get_channels, delete_channel
from keyboards import (
    channels_keyboard, channels_list_keyboard, channel_type_keyboard,
    back_keyboard, main_admin_keyboard
)
from states import set_state, clear_state, get_data, update_data
import states as st


async def channels_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = await get_channels()
    text = (
        f"🔐 <b>Majburiy obuna kanallar:</b>"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=channels_keyboard()
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=channels_keyboard()
        )


async def start_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔐 <b>Majburiy obuna turini tanlang:</b>\n\n"
        "Quyida majburiy obunani qo'shishning 3 ta turi mavjud:\n\n"
        "💠 <b>Ommaviy / Shaxsiy (Kanal · Guruh)</b>\n"
        "Har qanday kanal yoki guruhni (ommaviy yoki shaxsiy) majburiy obunaga ulash.\n\n"
        "💠 <b>Shaxsiy / So'rovli havola</b>\n"
        "Shaxsiy yoki so'rovli kanal/guruh havolasi orqali o'tganlarni kuzatish.\n\n"
        "💠 <b>🌐 Oddiy havola</b>\n"
        "Majburiy tekshiruvsiz oddiy havolani ko'rsatish (Instagram, sayt va boshqalar).",
        parse_mode="HTML",
        reply_markup=channel_type_keyboard()
    )


async def set_channel_type(update: Update, context: ContextTypes.DEFAULT_TYPE, ch_type: str):
    user_id = update.effective_user.id
    type_map = {
        'public': 'public',
        'private': 'private',
        'link': 'link'
    }
    update_data(user_id, ch_type=type_map.get(ch_type, 'public'))
    set_state(user_id, st.WAITING_CHANNEL_ID)

    if ch_type == 'link':
        await update.callback_query.edit_message_text(
            "🌐 Havolani yuboring:\n(Misol: https://instagram.com/yourpage)",
            reply_markup=back_keyboard("ch_add")
        )
    else:
        await update.callback_query.edit_message_text(
            "📢 Kanal/Guruh ID yoki username yuboring:\n\n"
            "Misol: @mychannel yoki -1001234567890\n\n"
            "💡 Botni kanalga admin qiling va ID ni yuboring!",
            reply_markup=back_keyboard("ch_add")
        )


async def handle_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    data = get_data(user_id)
    ch_type = data.get('ch_type', 'public')

    if ch_type == 'link':
        # Havola uchun
        update_data(user_id, channel_id=text, channel_link=text)
        set_state(user_id, st.WAITING_CHANNEL_NAME)
        await update.message.reply_text(
            "✅ Havola saqlandi.\n\nKanal/Sahifa nomini yuboring:"
        )
    else:
        update_data(user_id, channel_id=text)
        set_state(user_id, st.WAITING_CHANNEL_NAME)
        await update.message.reply_text(
            f"✅ ID: <code>{text}</code>\n\nKanal nomini yuboring:",
            parse_mode="HTML"
        )


async def handle_channel_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    data = get_data(user_id)
    ch_type = data.get('ch_type', 'public')

    if ch_type == 'link':
        channel_id = data.get('channel_id', '')
        channel_link = data.get('channel_link', '')
        await add_channel(channel_id, name, channel_link, 'link')
        clear_state(user_id)
        await update.message.reply_text(
            f"✅ Havola qo'shildi!\n🌐 {name}",
            reply_markup=main_admin_keyboard()
        )
    else:
        update_data(user_id, channel_name=name)
        set_state(user_id, st.WAITING_CHANNEL_LINK)
        await update.message.reply_text(
            f"✅ Nom: <b>{name}</b>\n\nKanal havolasini yuboring:\n"
            "(Misol: https://t.me/mychannel)\n"
            "Yoki '-' yuboring o'tkazib yuborish uchun",
            parse_mode="HTML"
        )


async def handle_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = update.message.text.strip()
    data = get_data(user_id)

    if link == '-':
        channel_id = data.get('channel_id', '')
        link = f"https://t.me/{channel_id.lstrip('@')}"

    channel_id = data.get('channel_id', '')
    channel_name = data.get('channel_name', '')
    ch_type = data.get('ch_type', 'public')

    await add_channel(channel_id, channel_name, link, ch_type)
    clear_state(user_id)

    await update.message.reply_text(
        f"✅ Kanal qo'shildi!\n"
        f"📢 {channel_name}\n"
        f"🔗 {link}",
        reply_markup=main_admin_keyboard()
    )


async def show_channel_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = await get_channels()
    if not channels:
        await update.callback_query.edit_message_text(
            "🔐 Kanallar yo'q",
            reply_markup=back_keyboard("channels")
        )
        return

    text = (
        f"📋 <b>Majburiy obuna kanallari ro'yxati:</b>\n\n"
        f"🔢 Jami: {len(channels)} ta\n\n"
        f"👇 Kerakli kanal ustiga bosib ma'lumotlarni ko'rishingiz mumkin."
    )
    await update.callback_query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=channels_list_keyboard(channels)
    )


async def show_channel_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, ch_id: str):
    channels = await get_channels()
    channel = None
    for ch in channels:
        if str(ch['id']) == str(ch_id):
            channel = ch
            break

    if not channel:
        await update.callback_query.edit_message_text("❌ Kanal topilmadi!")
        return

    text = (
        f"⚙️ <b>{channel['channel_name'] or channel['channel_id']}</b>\n\n"
        f"🆔 ID: <code>{channel['channel_id']}</code>\n"
        f"🔗 Havola: {channel['channel_link'] or 'Yo\'q'}\n"
        f"📁 Tur: {channel['channel_type']}\n"
        f"📅 Qo'shilgan: {channel['added_at'][:10]}"
    )
    from keyboards import confirm_keyboard
    await update.callback_query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=confirm_keyboard(
            f"ch_del_confirm_{channel['channel_id']}",
            "ch_list"
        )
    )


async def start_delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = await get_channels()
    if not channels:
        await update.callback_query.edit_message_text(
            "🗑 O'chiriladigan kanal yo'q",
            reply_markup=back_keyboard("channels")
        )
        return
    await update.callback_query.edit_message_text(
        "🗑 O'chirish uchun kanalni tanlang:",
        reply_markup=channels_list_keyboard(channels)
    )


async def do_delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, ch_id: str):
    await delete_channel(ch_id)
    await update.callback_query.edit_message_text(
        "✅ Kanal o'chirildi!",
        reply_markup=back_keyboard("channels")
    )
