import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import get_all_user_ids
from keyboards import broadcast_type_keyboard, back_keyboard, main_admin_keyboard
from states import set_state, clear_state, get_data, update_data
import states as st


async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📨 <b>Foydalanuvchilarga yuboradigan xabar turini tanlang.</b>"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=broadcast_type_keyboard()
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=broadcast_type_keyboard()
        )


async def set_broadcast_normal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_data(user_id, bc_type='normal')
    set_state(user_id, st.WAITING_BROADCAST_MSG)
    await update.callback_query.edit_message_text(
        "💬 Xabar yuboring:\n\n"
        "Text, rasm, video, audio yuborishingiz mumkin.",
        reply_markup=back_keyboard("broadcast")
    )


async def set_broadcast_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_data(user_id, bc_type='forward')
    set_state(user_id, st.WAITING_BROADCAST_MSG)
    await update.callback_query.edit_message_text(
        "📨 Forward qilmoqchi bo'lgan xabarni yuboring:",
        reply_markup=back_keyboard("broadcast")
    )


async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_data(user_id)
    bc_type = data.get('bc_type', 'normal')

    # Xabarni saqlash
    msg = update.message
    update_data(user_id, message_id=msg.message_id, chat_id=msg.chat_id, bc_type=bc_type)

    user_ids = await get_all_user_ids()
    total = len(user_ids)

    await update.message.reply_text(
        f"📨 Yuborish boshlandi...\n"
        f"👥 Jami foydalanuvchilar: {total}\n\n"
        f"Iltimos kuting..."
    )

    success = 0
    fail = 0

    for uid in user_ids:
        try:
            if bc_type == 'forward':
                await context.bot.forward_message(
                    chat_id=uid,
                    from_chat_id=msg.chat_id,
                    message_id=msg.message_id
                )
            else:
                await _copy_message(context.bot, msg, uid)
            success += 1
        except TelegramError:
            fail += 1
        await asyncio.sleep(0.05)  # Rate limit

    clear_state(user_id)
    await update.message.reply_text(
        f"✅ <b>Yuborish tugadi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xatolik: {fail}\n"
        f"👥 Jami: {total}",
        parse_mode="HTML",
        reply_markup=main_admin_keyboard()
    )


async def _copy_message(bot, msg, chat_id: int):
    """Xabarni nusxalab yuborish"""
    if msg.text:
        await bot.send_message(chat_id, msg.text, parse_mode="HTML")
    elif msg.photo:
        await bot.send_photo(
            chat_id, msg.photo[-1].file_id,
            caption=msg.caption or ""
        )
    elif msg.video:
        await bot.send_video(
            chat_id, msg.video.file_id,
            caption=msg.caption or ""
        )
    elif msg.document:
        await bot.send_document(
            chat_id, msg.document.file_id,
            caption=msg.caption or ""
        )
    elif msg.audio:
        await bot.send_audio(
            chat_id, msg.audio.file_id,
            caption=msg.caption or ""
        )
    elif msg.voice:
        await bot.send_voice(chat_id, msg.voice.file_id)
    elif msg.sticker:
        await bot.send_sticker(chat_id, msg.sticker.file_id)
    elif msg.animation:
        await bot.send_animation(
            chat_id, msg.animation.file_id,
            caption=msg.caption or ""
        )
    else:
        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
