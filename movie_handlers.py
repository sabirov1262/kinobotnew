from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import (
    add_movie, get_movie, get_all_movies, delete_movie, update_movie, get_setting
)
from keyboards import (
    movies_keyboard, movie_list_keyboard, movie_manage_keyboard,
    back_keyboard, main_admin_keyboard, confirm_keyboard
)
from states import set_state, clear_state, get_data, update_data
import states as st
from config import MOVIES_CHANNEL_ID


async def movies_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎬 <b>Kinolar bo'limidasiz:</b>\n\n"
        "Kinolar Telegram baza kanalga saqlanadi."
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=movies_keyboard()
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=movies_keyboard()
        )


async def start_add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_state(user_id, st.WAITING_MOVIE_CODE)
    await update.callback_query.edit_message_text(
        "📥 <b>Kino yuklash</b>\n\n"
        "1️⃣ Kino kodini yuboring:\n"
        "(Misol: 001, film1, avatar2)\n\n"
        "⚠️ Kod noyob bo'lishi kerak!",
        parse_mode="HTML",
        reply_markup=back_keyboard("movies")
    )


async def handle_movie_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = (update.message.text or "").strip().lower()

    if not code or len(code) > 50:
        await update.message.reply_text("❌ Kod 1-50 belgi bo'lishi kerak!")
        return

    existing = await get_movie(code)
    if existing:
        await update.message.reply_text(
            f"❌ '{code}' kodi allaqachon mavjud! Boshqa kod kiriting."
        )
        return

    update_data(user_id, code=code)
    set_state(user_id, st.WAITING_MOVIE_FILE)
    await update.message.reply_text(
        f"✅ Kod: <code>{code}</code>\n\n"
        f"2️⃣ Endi kino faylini yuboring:\n\n"
        f"📹 Video, 📄 Document, 🖼 Photo yoki GIF yuborish mumkin.\n"
        f"💡 Kino captioni bo'lsa, o'sha holatda baza kanalga saqlanadi.",
        parse_mode="HTML"
    )


async def handle_movie_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Bu versiyada alohida nom so'ralmaydi. Faylni yuboring.")


async def handle_movie_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Bu versiyada alohida tavsif so'ralmaydi. Faylni yuboring.")


async def handle_movie_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_data(user_id)
    code = data.get('code')

    if not code:
        await update.message.reply_text("❌ Xatolik! Qaytadan boshlang.")
        clear_state(user_id)
        return

    if not MOVIES_CHANNEL_ID:
        await update.message.reply_text(
            "❌ MOVIES_CHANNEL_ID sozlanmagan. Render environment ga baza kanal ID sini kiriting.\n"
            "Masalan: -1001234567890"
        )
        return

    file_id = None
    file_type = 'video'

    if update.message.video:
        file_id = update.message.video.file_id
        file_type = 'video'
    elif update.message.document:
        file_id = update.message.document.file_id
        file_type = 'document'
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = 'photo'
    elif update.message.animation:
        file_id = update.message.animation.file_id
        file_type = 'animation'
    else:
        await update.message.reply_text(
            "❌ Fayl topilmadi! Video, Document, Photo yoki GIF yuboring."
        )
        return

    caption = update.message.caption or ''
    title = code

    try:
        copied = await context.bot.copy_message(
            chat_id=MOVIES_CHANNEL_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
    except TelegramError as e:
        await update.message.reply_text(
            "❌ Kinoni baza kanalga saqlab bo'lmadi.\n"
            "Bot kanalga admin qilinganini tekshiring.\n\n"
            f"Xatolik: {e}"
        )
        return

    await add_movie(
        code=code,
        title=title,
        file_id=file_id,
        file_type=file_type,
        caption=caption,
        source_chat_id=str(MOVIES_CHANNEL_ID),
        source_message_id=copied.message_id,
    )
    clear_state(user_id)

    await update.message.reply_text(
        f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
        f"🔑 Kod: <code>{code}</code>\n"
        f"📁 Tur: {file_type}\n"
        f"🗂 Baza kanal xabari ID: <code>{copied.message_id}</code>",
        parse_mode="HTML",
        reply_markup=main_admin_keyboard()
    )


async def show_movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movies = await get_all_movies()
    if not movies:
        await update.callback_query.edit_message_text(
            "🎬 Kinolar yo'q",
            reply_markup=back_keyboard("movies")
        )
        return

    await update.callback_query.edit_message_text(
        f"🎬 <b>Kinolar ro'yxati ({len(movies)} ta):</b>\n\n"
        f"Kino ustiga bosib boshqarish mumkin.",
        parse_mode="HTML",
        reply_markup=movie_list_keyboard(movies)
    )


async def show_movie_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    movie = await get_movie(code)
    if not movie:
        await update.callback_query.edit_message_text(
            "❌ Kino topilmadi!", reply_markup=back_keyboard("movie_list")
        )
        return

    text = (
        f"🎬 <b>{movie['title']}</b>\n\n"
        f"🔑 Kod: <code>{movie['code']}</code>\n"
        f"📁 Tur: {movie['file_type']}\n"
        f"👁 Ko'rishlar: {movie['views']}\n"
        f"📝 Caption: {movie['caption'] or 'Yo\'q'}\n"
        f"🗂 Source chat: <code>{movie['source_chat_id'] or '-'}</code>\n"
        f"🧾 Source msg id: <code>{movie['source_message_id'] or '-'}</code>\n"
        f"📅 Qo'shilgan: {movie['added_at'][:10]}"
    )
    await update.callback_query.edit_message_text(
        text, parse_mode="HTML", reply_markup=movie_manage_keyboard(code)
    )


async def start_edit_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_state(user_id, st.WAITING_MOVIE_EDIT_CODE)
    await update.callback_query.edit_message_text(
        "✏️ Tahrirlash uchun kino kodini yuboring:",
        reply_markup=back_keyboard("movies")
    )


async def handle_edit_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = (update.message.text or "").strip().lower()
    movie = await get_movie(code)
    if not movie:
        await update.message.reply_text("❌ Kino topilmadi!")
        return

    await update.message.reply_text(
        f"🎬 <b>{movie['title']}</b>\n\nNimani tahrirlash?",
        parse_mode="HTML",
        reply_markup=movie_manage_keyboard(code)
    )
    clear_state(user_id)


async def edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    user_id = update.effective_user.id
    update_data(user_id, code=code, field='title')
    set_state(user_id, st.WAITING_MOVIE_EDIT_VALUE)
    await update.callback_query.edit_message_text(
        "✏️ Yangi nomni yuboring:",
        reply_markup=back_keyboard(f"mv_{code}")
    )


async def edit_caption(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    user_id = update.effective_user.id
    update_data(user_id, code=code, field='caption')
    set_state(user_id, st.WAITING_MOVIE_EDIT_VALUE)
    await update.callback_query.edit_message_text(
        "📝 Yangi captionni yuboring:",
        reply_markup=back_keyboard(f"mv_{code}")
    )


async def handle_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_data(user_id)
    code = data.get('code')
    field = data.get('field')
    value = (update.message.text or '').strip()

    await update_movie(code, field, value)
    clear_state(user_id)
    await update.message.reply_text("✅ O'zgartirildi!", reply_markup=main_admin_keyboard())


async def start_delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_state(user_id, st.WAITING_MOVIE_DELETE_CODE)
    await update.callback_query.edit_message_text(
        "🗑 O'chirish uchun kino kodini yuboring:",
        reply_markup=back_keyboard("movies")
    )


async def handle_delete_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = (update.message.text or '').strip().lower()
    movie = await get_movie(code)
    if not movie:
        await update.message.reply_text("❌ Kino topilmadi!")
        return
    clear_state(user_id)
    await update.message.reply_text(
        f"🗑 <b>{movie['title']}</b> ni o'chirishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard(f"mv_del_confirm_{code}", "movies")
    )


async def confirm_delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    movie = await get_movie(code)
    if not movie:
        await update.callback_query.edit_message_text("❌ Kino topilmadi!")
        return
    await update.callback_query.edit_message_text(
        f"🗑 <b>{movie['title']}</b> ni o'chirishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard(f"mv_del_confirm_{code}", "movies")
    )


async def do_delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    await delete_movie(code)
    await update.callback_query.edit_message_text(
        "✅ Kino o'chirildi!",
        reply_markup=back_keyboard("movies")
    )
