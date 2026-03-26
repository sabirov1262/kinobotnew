from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_user_count, get_movie_count, get_total_views, get_premium_user_count,
    get_premium_users, get_admins, add_admin, remove_admin, get_setting,
    set_setting, get_user, set_premium, remove_premium, is_admin
)
from keyboards import (
    admins_keyboard, settings_keyboard, premium_settings_keyboard,
    back_keyboard, main_admin_keyboard
)
from states import set_state, clear_state, get_state, get_data, update_data
import states as st
from config import SUPER_ADMIN_ID


async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_count = await get_user_count()
    movie_count = await get_movie_count()
    total_views = await get_total_views()
    premium_count = await get_premium_user_count()

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{user_count}</b>\n"
        f"🎬 Jami kinolar: <b>{movie_count}</b>\n"
        f"👁 Jami ko'rishlar: <b>{total_views}</b>\n"
        f"⭐ Premium foydalanuvchilar: <b>{premium_count}</b>\n"
    )

    if update.callback_query:
        from keyboards import admin_panel_inline
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=admin_panel_inline()
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=main_admin_keyboard()
        )


async def admins_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👮 <b>Adminlar bo'limidasiz:</b>\n\n"
        "💠 Bu yerda yangi admin qo'shishingiz yoki mavjudlarini boshqarishingiz mumkin."
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=admins_keyboard()
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=admins_keyboard()
        )


async def start_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_state(user_id, st.WAITING_ADMIN_ID)
    await update.callback_query.edit_message_text(
        "👮 Admin qo'shish\n\n"
        "Yangi adminning Telegram ID sini yuboring:\n"
        "(Misol: 123456789)",
        reply_markup=back_keyboard("admins")
    )


async def handle_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        new_admin_id = int(text)
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID! Faqat raqam kiriting.")
        return

    if new_admin_id == SUPER_ADMIN_ID:
        await update.message.reply_text("❌ Bu super admin!")
        return

    try:
        chat = await context.bot.get_chat(new_admin_id)
        name = chat.full_name or str(new_admin_id)
        username = chat.username or ""
    except Exception:
        name = str(new_admin_id)
        username = ""

    await add_admin(new_admin_id, username, name)
    clear_state(user_id)

    await update.message.reply_text(
        f"✅ Admin qo'shildi!\n👤 {name} ({new_admin_id})",
        reply_markup=main_admin_keyboard()
    )


async def start_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_state(user_id, st.WAITING_ADMIN_REMOVE_ID)
    await update.callback_query.edit_message_text(
        "👮 Adminni o'chirish\n\n"
        "O'chirmoqchi bo'lgan adminning Telegram ID sini yuboring:",
        reply_markup=back_keyboard("admins")
    )


async def handle_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        rm_id = int(text)
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID!")
        return

    await remove_admin(rm_id)
    clear_state(user_id)
    await update.message.reply_text("✅ Admin o'chirildi!", reply_markup=main_admin_keyboard())


async def show_admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = await get_admins()
    if not admins:
        text = "👮 Adminlar yo'q"
    else:
        text = "👮 <b>Adminlar ro'yxati:</b>\n\n"
        for i, a in enumerate(admins, 1):
            text += f"{i}. {a['full_name']} — <code>{a['user_id']}</code>\n"
    await update.callback_query.edit_message_text(
        text, parse_mode="HTML", reply_markup=back_keyboard("admins")
    )


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sharing = await get_setting('sharing_enabled')
    sharing_on = sharing == '1'
    text = "⚙️ <b>Sozlamalar bo'limidasiz:</b>"
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=settings_keyboard(sharing_on)
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=settings_keyboard(sharing_on)
        )


async def toggle_sharing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = await get_setting('sharing_enabled')
    new_val = '0' if current == '1' else '1'
    await set_setting('sharing_enabled', new_val)
    await settings_menu(update, context)


async def payment_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from keyboards import payment_settings_keyboard
    await update.callback_query.edit_message_text(
        "⚙️ <b>To'lov tizim sozlamalaridasiz:</b>",
        parse_mode="HTML",
        reply_markup=payment_settings_keyboard()
    )


async def premium_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    premium_on = await get_setting('premium_enabled')
    prem_count = await get_premium_user_count()

    text = (
        f"⚙️ <b>Premium sozlamalar bo'limidasiz:</b>\n\n"
        f"💠 Premium holati: {'✅ Faol' if premium_on == '1' else '❌ Nofaol'}\n"
        f"👥 Jami Premium foydalanuvchilar: {prem_count} ta\n\n"
        f"📌 Quyidagi tugmalardan foydalanib Premium sozlamalarini boshqaring."
    )
    await update.callback_query.edit_message_text(
        text, parse_mode="HTML", reply_markup=premium_settings_keyboard()
    )


async def toggle_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = await get_setting('premium_enabled')
    new_val = '0' if current == '1' else '1'
    await set_setting('premium_enabled', new_val)
    await premium_settings_menu(update, context)


async def show_premium_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = await get_premium_users()
    if not users:
        text = "👥 Premium foydalanuvchilar yo'q"
    else:
        text = f"👥 <b>Premium foydalanuvchilar ({len(users)} ta):</b>\n\n"
        for i, u in enumerate(users, 1):
            expire = u['premium_expire'] or 'Cheksiz'
            text += f"{i}. {u['full_name']} — {u['user_id']}\n   📅 {expire}\n"
    await update.callback_query.edit_message_text(
        text, parse_mode="HTML", reply_markup=back_keyboard("premium_settings")
    )


async def start_give_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_state(user_id, st.WAITING_GIVE_PREMIUM_ID)
    await update.callback_query.edit_message_text(
        "⭐ Premium berish\n\nFoydalanuvchi ID sini yuboring:",
        reply_markup=back_keyboard("premium_settings")
    )


async def handle_give_premium_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    try:
        target_id = int(text)
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID!")
        return

    update_data(user_id, target_id=target_id)
    set_state(user_id, st.WAITING_GIVE_PREMIUM_DAYS)
    await update.message.reply_text(
        f"✅ Foydalanuvchi: {target_id}\n\nNecha kunlik premium bermoqchisiz? (raqam kiriting)"
    )


async def handle_give_premium_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    try:
        days = int(text)
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri raqam!")
        return

    data = get_data(user_id)
    target_id = data.get('target_id')

    if not target_id:
        await update.message.reply_text("❌ Xatolik! Qaytadan boshlang.")
        clear_state(user_id)
        return

    await set_premium(target_id, days)
    clear_state(user_id)

    # Foydalanuvchiga xabar
    try:
        await context.bot.send_message(
            target_id,
            f"🎉 Sizga {days} kunlik Premium berildi!\n\n"
            f"Premium imtiyozlaridan bahramand bo'ling! ⭐"
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ {target_id} ga {days} kunlik Premium berildi!",
        reply_markup=main_admin_keyboard()
    )
