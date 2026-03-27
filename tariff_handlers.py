from telegram import Update
from telegram.ext import ContextTypes

from database import (
    add_tariff, get_tariffs, get_tariff, update_tariff, delete_tariff as db_delete_tariff
)
from keyboards import (
    tariff_list_keyboard, tariff_manage_keyboard, back_keyboard, main_admin_keyboard
)
from states import set_state, clear_state, get_data, update_data
import states as st


async def show_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tariffs = await get_tariffs()
    if not tariffs:
        names = "Tariflar yo'q"
    else:
        names = " • ".join([t['name'] for t in tariffs])

    text = f"📋 <b>Premium tariflar ro'yxati:</b>\n\n🟢 {names}" if tariffs else "📋 Tariflar yo'q"

    await update.callback_query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=tariff_list_keyboard(tariffs)
    )


async def show_tariff_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, tariff_id: int):
    tariff = await get_tariff(tariff_id)
    if not tariff:
        await update.callback_query.edit_message_text("❌ Tarif topilmadi!")
        return

    text = (
        f"📦 <b>{tariff['name']}</b>\n\n"
        f"📅 Muddat: {tariff['duration_days']} kun\n"
        f"💰 Narx: {tariff['price']:,} so'm\n"
        f"💠 Holat: {'🟢 Faol' if tariff['is_active'] else '🔴 Nofaol'}"
    )
    await update.callback_query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=tariff_manage_keyboard(tariff_id)
    )


async def start_add_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_state(user_id, st.WAITING_TARIFF_NAME)
    await update.callback_query.edit_message_text(
        "➕ <b>Tarif qo'shish</b>\n\nTarif nomini yuboring:\n(Misol: 1 oylik obuna)",
        parse_mode="HTML",
        reply_markup=back_keyboard("premium_tariffs")
    )


async def handle_tariff_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    update_data(user_id, tariff_name=name)
    set_state(user_id, st.WAITING_TARIFF_DAYS)
    await update.message.reply_text(
        f"✅ Nom: <b>{name}</b>\n\nNecha kunlik? (raqam kiriting)",
        parse_mode="HTML"
    )


async def handle_tariff_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        days = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Raqam kiriting!")
        return

    update_data(user_id, tariff_days=days)
    set_state(user_id, st.WAITING_TARIFF_PRICE)
    await update.message.reply_text(
        f"✅ Muddat: <b>{days} kun</b>\n\nNarxini kiriting (so'm):",
        parse_mode="HTML"
    )


async def handle_tariff_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        price = int(update.message.text.strip().replace(' ', '').replace(',', ''))
    except ValueError:
        await update.message.reply_text("❌ Narxni raqamda kiriting!")
        return

    data = get_data(user_id)
    name = data.get('tariff_name', '')
    days = data.get('tariff_days', 30)

    await add_tariff(name, days, price)
    clear_state(user_id)

    await update.message.reply_text(
        f"✅ <b>Tarif qo'shildi!</b>\n\n"
        f"📦 {name}\n"
        f"📅 {days} kun\n"
        f"💰 {price:,} so'm",
        parse_mode="HTML",
        reply_markup=main_admin_keyboard()
    )


async def edit_tariff_field(update: Update, context: ContextTypes.DEFAULT_TYPE, tariff_id: int, field: str):
    user_id = update.effective_user.id
    update_data(user_id, tariff_id=tariff_id, field=field)
    set_state(user_id, st.WAITING_TARIFF_EDIT_VALUE)

    field_names = {
        'name': 'yangi nom',
        'duration_days': 'yangi muddat (kun)',
        'price': 'yangi narx (so\'m)'
    }
    await update.callback_query.edit_message_text(
        f"✏️ {field_names.get(field, field)}ni yuboring:",
        reply_markup=back_keyboard(f"tariff_{tariff_id}")
    )


async def handle_tariff_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_data(user_id)
    tariff_id = data.get('tariff_id')
    field = data.get('field')
    value = update.message.text.strip()

    if field in ['duration_days', 'price']:
        try:
            value = int(value.replace(' ', '').replace(',', ''))
        except ValueError:
            await update.message.reply_text("❌ Raqam kiriting!")
            return

    await update_tariff(tariff_id, field, value)
    clear_state(user_id)
    await update.message.reply_text("✅ O'zgartirildi!", reply_markup=main_admin_keyboard())


async def toggle_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE, tariff_id: int):
    tariff = await get_tariff(tariff_id)
    new_status = 0 if tariff['is_active'] else 1
    await update_tariff(tariff_id, 'is_active', new_status)
    await show_tariff_detail(update, context, tariff_id)


async def delete_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE, tariff_id: int):
    await db_delete_tariff(tariff_id)
    await update.callback_query.edit_message_text(
        "✅ Tarif o'chirildi!",
        reply_markup=back_keyboard("premium_tariffs")
    )
