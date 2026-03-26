from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from asyncpg import UniqueViolationError

from config import settings
from keyboards import back_only_kb, movies_menu_kb
from states import AddMovieState, MovieDeleteState, MovieSearchState

router = Router()
logger = logging.getLogger(__name__)


def admin_only(message: Message) -> bool:
    return message.from_user.id == settings.super_admin_id


@router.message(F.text == "📥 Kino yuklash")
async def start_add_movie(message: Message, state: FSMContext):
    if not admin_only(message):
        return
    await state.set_state(AddMovieState.waiting_code)
    await message.answer(
        "📥 Kino yuklash\n\n"
        "1️⃣ Kino kodini yuboring.\n"
        "Misol: 100, kino77 yoki avatar2\n\n"
        "Kod noyob bo‘lishi kerak.",
        reply_markup=back_only_kb(),
    )


@router.message(AddMovieState.waiting_code)
async def receive_movie_code(message: Message, state: FSMContext, db):
    code = (message.text or "").strip()
    if code == "◀️ Orqaga":
        await state.clear()
        await message.answer("🎬 Kinolar bo‘limi", reply_markup=movies_menu_kb())
        return

    if not code:
        await message.answer("❌ Kod bo‘sh bo‘lmasin.")
        return

    existing = await db.get_movie_by_code(code)
    if existing:
        await message.answer("❌ Bu kod allaqachon mavjud. Boshqa kod yuboring.")
        return

    await state.update_data(code=code)
    await state.set_state(AddMovieState.waiting_media)
    await message.answer(
        f"✅ Kod qabul qilindi: {code}\n\n"
        "2️⃣ Endi kinoni yuboring.\n\n"
        "📹 Video yoki 📄 Document yuborish mumkin.",
        reply_markup=back_only_kb(),
    )


@router.message(AddMovieState.waiting_media, F.video | F.document)
async def receive_movie_media(message: Message, state: FSMContext, db):
    if not admin_only(message):
        return

    data = await state.get_data()
    code = data["code"]
    file_type = "video" if message.video else "document"

    try:
        # Message.copy_to returns the sent Message object, which includes the new message_id.
        sent = await message.copy_to(
            chat_id=settings.channel_id,
            protect_content=False,
        )
        await db.add_movie(
            code=code,
            channel_message_id=sent.message_id,
            file_type=file_type,
            caption=message.caption,
        )
    except UniqueViolationError:
        await message.answer("❌ Bu kod allaqachon mavjud.")
        await state.clear()
        return
    except Exception as exc:
        logger.exception("Kino saqlashda xatolik: %s", exc)
        await message.answer(
            "❌ Kinoni saqlashda xatolik yuz berdi.\n"
            "Bot kanalga admin qilinganini va CHANNEL_ID to‘g‘ri ekanini tekshiring."
        )
        await state.clear()
        return

    await message.answer(
        "✅ Kino saqlandi!\n\n"
        f"🔢 Kod: {code}\n"
        f"🆔 Channel message_id: {sent.message_id}",
        reply_markup=movies_menu_kb(),
    )
    await state.clear()


@router.message(AddMovieState.waiting_media)
async def wrong_media(message: Message):
    await message.answer("❌ Iltimos, video yoki document yuboring.")


@router.message(F.text == "🔍 Kod bo‘yicha qidirish")
async def ask_search_code(message: Message, state: FSMContext):
    if not admin_only(message):
        return
    await state.set_state(MovieSearchState.waiting_code)
    await message.answer("🔍 Qidirish uchun kino kodini yuboring.", reply_markup=back_only_kb())


@router.message(MovieSearchState.waiting_code)
async def search_code(message: Message, state: FSMContext, db):
    code = (message.text or "").strip()
    if code == "◀️ Orqaga":
        await state.clear()
        await message.answer("🎬 Kinolar bo‘limi", reply_markup=movies_menu_kb())
        return

    movie = await db.get_movie_by_code(code)
    if movie:
        await message.answer(
            "✅ Kino topildi\n\n"
            f"🔢 Kod: {movie['code']}\n"
            f"🆔 Channel message_id: {movie['channel_message_id']}"
        )
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")
    await state.clear()
    await message.answer("🎬 Kinolar bo‘limi", reply_markup=movies_menu_kb())


@router.message(F.text == "🗑 Kino o‘chirish")
async def ask_delete_code(message: Message, state: FSMContext):
    if not admin_only(message):
        return
    await state.set_state(MovieDeleteState.waiting_code)
    await message.answer("🗑 O‘chirish uchun kino kodini yuboring.", reply_markup=back_only_kb())


@router.message(MovieDeleteState.waiting_code)
async def delete_code(message: Message, state: FSMContext, db):
    code = (message.text or "").strip()
    if code == "◀️ Orqaga":
        await state.clear()
        await message.answer("🎬 Kinolar bo‘limi", reply_markup=movies_menu_kb())
        return

    result = await db.delete_movie_by_code(code)
    await state.clear()
    if result.endswith("DELETE 1"):
        await message.answer("✅ Kino o‘chirildi.", reply_markup=movies_menu_kb())
    else:
        await message.answer("❌ Bunday kod topilmadi.", reply_markup=movies_menu_kb())


@router.message(F.text == "📚 Kinolar ro‘yxati")
async def list_movies(message: Message, db):
    if not admin_only(message):
        return
    items = await db.list_movies(limit=20)
    if not items:
        await message.answer("📚 Hozircha kinolar yo‘q.", reply_markup=movies_menu_kb())
        return

    lines = ["📚 So‘nggi kinolar ro‘yxati:\n"]
    for item in items:
        lines.append(f"• {item['code']} — #{item['channel_message_id']}")
    await message.answer("\n".join(lines), reply_markup=movies_menu_kb())


@router.message(F.text.regexp(r"^[A-Za-z0-9_]+$"))
async def send_movie_by_code(message: Message, db):
    # User or admin can request movie directly by code from main chat.
    text = (message.text or "").strip()
    if text in {"BOT", "HTML"}:
        return
    movie = await db.get_movie_by_code(text)
    if not movie:
        return

    protect_content = await db.get_setting("protect_content", "0")
    try:
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=settings.channel_id,
            message_id=movie["channel_message_id"],
            protect_content=(protect_content == "1"),
        )
    except Exception as exc:
        logger.exception("Kinoni userga yuborishda xatolik: %s", exc)
        await message.answer("❌ Kinoni yuborib bo‘lmadi.")
