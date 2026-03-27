from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, BadRequest

from database import (
    add_user, is_admin, get_setting, get_channels, get_movie, increment_views,
    get_tariffs, get_tariff, is_premium_user, create_premium_request,
    get_user_premium_requests, get_pending_premium_requests, get_premium_request,
    update_premium_request_status, set_premium, get_admins
)
from keyboards import (
    main_admin_keyboard, main_user_keyboard, subscribe_keyboard,
    user_premium_keyboard, tariff_list_keyboard, user_tariff_keyboard,
    premium_request_admin_keyboard, back_keyboard,
)
from states import get_state, clear_state, set_state, get_data, update_data
import states as st
import admin_handlers as adm
import movie_handlers as mv_h
import channel_handlers as ch_h
import tariff_handlers as tr_h
import broadcast_handlers as bc_h
from config import PROTECT_CONTENT_DEFAULT, PAYMENT_CARD, PAYMENT_OWNER, SUPPORT_USERNAME

MENU_TEXTS = {
    "📊 Statistika", "📨 Xabar yuborish", "🎬 Kinolar", "🔐 Kanallar", "👮 Adminlar", "⚙️ Sozlamalar",
    "⭐ Premium", "👤 Kabinet", "ℹ️ Yordam", "🎬 Kino kodini yuborish", "❌ Bekor qilish"
}


async def safe_edit_text(query, text, reply_markup=None, parse_mode="HTML"):
    try:
        kwargs = {"text": text, "reply_markup": reply_markup}
        if parse_mode is not None:
            kwargs["parse_mode"] = parse_mode
        await query.edit_message_text(**kwargs)
    except BadRequest as e:
        err = str(e)

        if "Message is not modified" in err:
            return

        if "message to edit not found" in err.lower():
            kwargs = {"text": text, "reply_markup": reply_markup}
            if parse_mode is not None:
                kwargs["parse_mode"] = parse_mode
            await query.message.reply_text(**kwargs)
            return

        raise


async def safe_edit_caption(query, caption, reply_markup=None, parse_mode="HTML"):
    try:
        kwargs = {"caption": caption, "reply_markup": reply_markup}
        if parse_mode is not None:
            kwargs["parse_mode"] = parse_mode
        await query.edit_message_caption(**kwargs)
    except BadRequest as e:
        err = str(e)

        if "Message is not modified" in err:
            return

        if "message to edit not found" in err.lower():
            kwargs = {"text": caption, "reply_markup": reply_markup}
            if parse_mode is not None:
                kwargs["parse_mode"] = parse_mode
            await query.message.reply_text(**kwargs)
            return

        raise


async def admin_check(user_id: int) -> bool:
    return await is_admin(user_id)


async def check_subscription(bot, user_id: int, channels: list) -> list:
    not_subscribed = []
    for ch in channels:
        ch_type = ch['channel_type']
        if ch_type == 'link':
            continue
        try:
            member = await bot.get_chat_member(ch['channel_id'], user_id)
            if member.status in ['left', 'kicked', 'banned']:
                not_subscribed.append(ch)
        except TelegramError:
            not_subscribed.append(ch)
    return not_subscribed


async def ensure_subscription_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    sub_required = await get_setting('subscription_required')
    if sub_required != '1':
        return True

    channels = await get_channels()
    if not channels:
        return True

    not_sub = await check_subscription(context.bot, update.effective_user.id, channels)
    if not not_sub:
        return True

    kb = subscribe_keyboard(not_sub)
    text = "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:"

    if update.callback_query:
        await safe_edit_text(update.callback_query, text, reply_markup=kb, parse_mode=None)
    elif update.message:
        await update.message.reply_text(text, reply_markup=kb)
    return False


async def _support_text() -> str:
    support = f"@{SUPPORT_USERNAME}" if SUPPORT_USERNAME else "admin"
    return (
        f"ℹ️ <b>Yordam</b>\n\n"
        f"1. Kino olish uchun kod yuboring.\n"
        f"2. Premium bo'limidan tarif tanlab so'rov yuboring.\n"
        f"3. Muammo bo'lsa {support} ga yozing."
    )


async def _user_profile_text(user_id: int, first_name: str) -> str:
    premium = await is_premium_user(user_id)
    reqs = await get_user_premium_requests(user_id)
    pending = sum(1 for r in reqs if r['status'] == 'pending')
    status = "⭐ Premium" if premium else "🆓 Oddiy foydalanuvchi"
    return (
        f"👤 <b>Kabinet</b>\n\n"
        f"Ism: <b>{first_name}</b>\n"
        f"ID: <code>{user_id}</code>\n"
        f"Holat: {status}\n"
        f"Premium so'rovlar: <b>{len(reqs)}</b>\n"
        f"Kutilayotganlari: <b>{pending}</b>"
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await add_user(user.id, user.username or "", user.full_name or "")
    clear_state(user.id)

    args = context.args
    if args:
        code = args[0].strip().lower()
        if not await ensure_subscription_prompt(update, context):
            return
        await send_movie(update, context, code)
        return

    is_adm = await admin_check(user.id)
    if not is_adm and not await ensure_subscription_prompt(update, context):
        return

    welcome = await get_setting('welcome_message')
    welcome = welcome.format(name=user.first_name) if welcome else (
        f"👋 Assalomu alaykum {user.first_name}!\n\n🎬 Kino kodini yuboring yoki menyudan foydalaning."
    )

    keyboard = main_admin_keyboard() if is_adm else main_user_keyboard()
    await update.message.reply_text(welcome, parse_mode="HTML", reply_markup=keyboard)


async def send_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    if not await ensure_subscription_prompt(update, context):
        return

    movie = await get_movie(code)
    if not movie:
        if update.message:
            await update.message.reply_text("❌ Bunday kodli kino topilmadi!")
        elif update.callback_query:
            await update.callback_query.message.reply_text("❌ Bunday kodli kino topilmadi!")
        return

    await increment_views(code)

    try:
        target_message = update.message or update.callback_query.message

        if movie['source_chat_id'] and movie['source_message_id']:
            protect = (await get_setting('sharing_enabled')) == '0' or PROTECT_CONTENT_DEFAULT
            await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=movie['source_chat_id'],
                message_id=movie['source_message_id'],
                protect_content=protect,
            )
            return

        caption = movie['caption'] or movie['title']
        ftype = movie['file_type']

        if ftype == 'video':
            await target_message.reply_video(
                movie['file_id'],
                caption=caption,
                protect_content=PROTECT_CONTENT_DEFAULT
            )
        elif ftype == 'document':
            await target_message.reply_document(
                movie['file_id'],
                caption=caption,
                protect_content=PROTECT_CONTENT_DEFAULT
            )
        elif ftype == 'photo':
            await target_message.reply_photo(
                movie['file_id'],
                caption=caption,
                protect_content=PROTECT_CONTENT_DEFAULT
            )
        elif ftype == 'animation':
            await target_message.reply_animation(
                movie['file_id'],
                caption=caption,
                protect_content=PROTECT_CONTENT_DEFAULT
            )
        else:
            await target_message.reply_text("❌ Kino fayli topilmadi.")
    except TelegramError as e:
        target_message = update.message or update.callback_query.message
        await target_message.reply_text(f"❌ Xatolik: {e}")


async def show_user_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    premium_enabled = await get_setting('premium_enabled')
    if premium_enabled != '1':
        text = "⭐ Premium hozircha o'chirilgan."
    else:
        text = (
            "⭐ <b>Premium bo'limi</b>\n\n"
            "Premium orqali reklamasiz va qulay foydalanish imkonlari ochiladi.\n"
            "Quyidagi tugmalardan birini tanlang."
        )

    markup = user_premium_keyboard()

    if update.callback_query:
        await safe_edit_text(update.callback_query, text, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def show_user_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tariffs = await get_tariffs()
    if not tariffs:
        text = "⭐ Hozircha faol tariflar yo'q."
        markup = back_keyboard("admin_back" if await admin_check(update.effective_user.id) else "user_premium")
    else:
        text = "📦 <b>Mavjud premium tariflar</b>\n\nTarif ustiga bosib batafsil ko'ring."
        markup = tariff_list_keyboard(tariffs, admin_mode=False)

    if update.callback_query:
        await safe_edit_text(update.callback_query, text, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def show_user_tariff_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, tariff_id: int):
    tariff = await get_tariff(tariff_id)
    if not tariff or not tariff['is_active']:
        await safe_edit_text(update.callback_query, "❌ Tarif topilmadi.", reply_markup=back_keyboard("user_premium"), parse_mode=None)
        return

    text = (
        f"📦 <b>{tariff['name']}</b>\n\n"
        f"📅 Muddat: <b>{tariff['duration_days']} kun</b>\n"
        f"💰 Narx: <b>{tariff['price']:,} so'm</b>\n\n"
        f"Sotib olish tugmasini bossangiz, to'lov ko'rsatmasi chiqadi."
    )
    await safe_edit_text(
        update.callback_query,
        text,
        reply_markup=user_tariff_keyboard(tariff_id),
        parse_mode="HTML"
    )


async def start_buy_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE, tariff_id: int):
    tariff = await get_tariff(tariff_id)
    if not tariff or not tariff['is_active']:
        await safe_edit_text(update.callback_query, "❌ Tarif topilmadi.", reply_markup=back_keyboard("user_premium"), parse_mode=None)
        return

    payment_card = (await get_setting('payment_card')) or PAYMENT_CARD
    payment_owner = (await get_setting('payment_owner')) or PAYMENT_OWNER
    payment_note = (await get_setting('payment_note')) or "To'lovdan keyin screenshot yuboring."

    update_data(update.effective_user.id, tariff_id=tariff_id)
    set_state(update.effective_user.id, st.WAITING_PREMIUM_SCREENSHOT)

    lines = [
        f"🛒 <b>{tariff['name']}</b>",
        f"📅 Muddat: {tariff['duration_days']} kun",
        f"💰 Narx: {tariff['price']:,} so'm",
        "",
    ]
    if payment_card:
        lines.append(f"💳 Karta: <code>{payment_card}</code>")
    if payment_owner:
        lines.append(f"👤 Egasi: <b>{payment_owner}</b>")
    if not payment_card:
        lines.append("⚠️ To'lov rekvizitlari hali sozlanmagan. Admin bilan bog'laning.")
    lines.extend([
        "",
        payment_note,
        "",
        "📸 Endi shu chatga to'lov screenshotini yuboring.",
        "❌ Bekor qilish tugmasi orqali jarayonni to'xtatishingiz mumkin.",
    ])

    await safe_edit_text(
        update.callback_query,
        "\n".join(lines),
        reply_markup=back_keyboard("user_premium"),
        parse_mode="HTML"
    )


async def handle_premium_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_data(user.id)
    tariff_id = data.get('tariff_id')
    tariff = await get_tariff(tariff_id) if tariff_id else None
    if not tariff:
        clear_state(user.id)
        await update.message.reply_text(
            "❌ Tarif topilmadi. Qaytadan urinib ko'ring.",
            reply_markup=main_user_keyboard()
        )
        return

    screenshot_file_id = None
    if update.message.photo:
        screenshot_file_id = update.message.photo[-1].file_id
    elif update.message.document:
        screenshot_file_id = update.message.document.file_id
    else:
        await update.message.reply_text("❌ Screenshot rasm yoki document ko'rinishida yuborilishi kerak.")
        return

    request_id = await create_premium_request(user.id, tariff_id, screenshot_file_id, note="manual payment")
    clear_state(user.id)

    request = await get_premium_request(request_id)
    text = (
        f"🧾 <b>Yangi premium so'rov</b>\n\n"
        f"👤 Foydalanuvchi: {request['full_name'] or user.full_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📦 Tarif: <b>{request['tariff_name']}</b>\n"
        f"📅 Muddat: {request['duration_days']} kun\n"
        f"💰 Narx: {request['price']:,} so'm\n"
        f"🧾 So'rov ID: <code>{request_id}</code>"
    )

    admins = [a['user_id'] for a in await get_admins()]
    from config import SUPER_ADMIN_ID
    if SUPER_ADMIN_ID:
        admins.append(SUPER_ADMIN_ID)
    admins = list(dict.fromkeys(admins))

    for admin_id in admins:
        try:
            await context.bot.send_photo(
                admin_id,
                screenshot_file_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=premium_request_admin_keyboard(request_id)
            )
        except Exception:
            try:
                await context.bot.send_message(
                    admin_id,
                    text,
                    parse_mode="HTML",
                    reply_markup=premium_request_admin_keyboard(request_id)
                )
            except Exception:
                pass

    await update.message.reply_text(
        "✅ So'rovingiz yuborildi. Admin tasdiqlagach premium avtomatik beriladi.",
        reply_markup=main_user_keyboard(),
    )


async def show_user_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reqs = await get_user_premium_requests(update.effective_user.id)
    if not reqs:
        text = "📨 Sizda premium so'rovlar yo'q."
    else:
        lines = ["📨 <b>So'rovlaringiz</b>"]
        for r in reqs[:10]:
            status_map = {'pending': '⏳ Kutilmoqda', 'approved': '✅ Tasdiqlangan', 'rejected': '❌ Bekor qilingan'}
            lines.append(f"\n• {r['tariff_name']} — {status_map.get(r['status'], r['status'])}")
        text = "\n".join(lines)

    await safe_edit_text(
        update.callback_query,
        text,
        reply_markup=back_keyboard("user_premium"),
        parse_mode="HTML"
    )


async def show_pending_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reqs = await get_pending_premium_requests()
    if not reqs:
        await safe_edit_text(
            update.callback_query,
            "🧾 Kutilayotgan premium so'rovlar yo'q.",
            reply_markup=back_keyboard("premium_settings"),
            parse_mode=None
        )
        return

    lines = ["🧾 <b>Kutilayotgan so'rovlar</b>"]
    for r in reqs[:20]:
        lines.append(f"\n• #{r['id']} — {r['full_name'] or r['user_id']} — {r['tariff_name']}")

    await safe_edit_text(
        update.callback_query,
        "\n".join(lines),
        reply_markup=back_keyboard("premium_settings"),
        parse_mode="HTML"
    )


async def approve_premium_request(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    req = await get_premium_request(request_id)
    if not req or req['status'] != 'pending':
        await update.callback_query.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await set_premium(req['user_id'], req['duration_days'])
    await update_premium_request_status(request_id, 'approved', update.effective_user.id)

    try:
        await context.bot.send_message(
            req['user_id'],
            f"🎉 Premium so'rovingiz tasdiqlandi!\n\n📦 {req['tariff_name']}\n📅 {req['duration_days']} kun"
        )
    except Exception:
        pass

    if update.callback_query.message.photo:
        old_caption = update.callback_query.message.caption or ""
        new_caption = old_caption + "\n\n✅ Tasdiqlandi"
        await safe_edit_caption(update.callback_query, new_caption, parse_mode="HTML")
    else:
        await safe_edit_text(update.callback_query, "✅ So'rov tasdiqlandi.", parse_mode=None)


async def reject_premium_request(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    req = await get_premium_request(request_id)
    if not req or req['status'] != 'pending':
        await update.callback_query.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await update_premium_request_status(request_id, 'rejected', update.effective_user.id)

    try:
        await context.bot.send_message(
            req['user_id'],
            "❌ Premium so'rovingiz bekor qilindi.\n\nSabab uchun admin bilan bog'laning."
        )
    except Exception:
        pass

    if update.callback_query.message.photo:
        old_caption = update.callback_query.message.caption or ""
        new_caption = old_caption + "\n\n❌ Bekor qilindi"
        await safe_edit_caption(update.callback_query, new_caption, parse_mode="HTML")
    else:
        await safe_edit_text(update.callback_query, "❌ So'rov bekor qilindi.", parse_mode=None)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    text = (update.message.text or "").strip()
    state = get_state(user.id)["state"]
    is_adm = await admin_check(user.id)

    if text == "❌ Bekor qilish":
        clear_state(user.id)
        await update.message.reply_text("✅ Bekor qilindi.", reply_markup=main_admin_keyboard() if is_adm else main_user_keyboard())
        return

    if state == st.WAITING_PREMIUM_SCREENSHOT:
        await handle_premium_screenshot(update, context)
        return

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
    elif text == "⭐ Premium":
        await show_user_premium_menu(update, context)
        return
    elif text == "👤 Kabinet":
        await update.message.reply_text(await _user_profile_text(user.id, user.first_name), parse_mode="HTML", reply_markup=main_admin_keyboard() if is_adm else main_user_keyboard())
        return
    elif text == "ℹ️ Yordam":
        await update.message.reply_text(await _support_text(), parse_mode="HTML", reply_markup=main_user_keyboard())
        return
    elif text == "🎬 Kino kodini yuborish" and not is_adm:
        await update.message.reply_text("🎬 Kino kodini yuboring. Masalan: <code>001</code>", parse_mode="HTML")
        return

    if state == st.WAITING_MOVIE_SOURCE_MESSAGE_ID:
        await mv_h.handle_movie_source_message_id(update, context)
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

    if not text or text in MENU_TEXTS or text.startswith('/'):
        return

    normalized = text.lower().strip()
    if len(normalized) <= 50 and all(ch.isalnum() or ch in {'_', '-'} for ch in normalized):
        await send_movie(update, context, normalized)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user
    is_adm = await admin_check(user.id)

    if data == "check_sub":
        ok = await ensure_subscription_prompt(update, context)
        if ok:
            await safe_edit_text(query, "✅ Rahmat! Endi kino kodini yuboring.", parse_mode=None)
        return

    # User callbacks
    if data == "user_premium":
        await show_user_tariffs(update, context)
        return
    if data == "user_premium_requests":
        await show_user_requests(update, context)
        return
    if data.startswith("user_tariff_"):
        await show_user_tariff_detail(update, context, int(data.replace("user_tariff_", "")))
        return
    if data.startswith("buy_tariff_"):
        await start_buy_tariff(update, context, int(data.replace("buy_tariff_", "")))
        return

    # Admin-only callbacks
    if data.startswith("premium_approve_"):
        if not is_adm:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        await approve_premium_request(update, context, int(data.replace("premium_approve_", "")))
        return
    if data.startswith("premium_reject_"):
        if not is_adm:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        await reject_premium_request(update, context, int(data.replace("premium_reject_", "")))
        return

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
    elif data.startswith("mv_del_confirm_"):
        code = data.replace("mv_del_confirm_", "")
        await mv_h.do_delete_movie(update, context, code)
    elif data.startswith("mv_del_"):
        code = data.replace("mv_del_", "")
        await mv_h.confirm_delete_movie(update, context, code)
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
        await ch_h.set_channel_type(update, context, data.replace("chtype_", ""))
    elif data == "ch_list":
        await ch_h.show_channel_list(update, context)
    elif data == "ch_delete":
        await ch_h.start_delete_channel(update, context)
    elif data.startswith("ch_del_confirm_"):
        await ch_h.do_delete_channel(update, context, data.replace("ch_del_confirm_", ""))
    elif data.startswith("ch_"):
        await ch_h.show_channel_detail(update, context, data.replace("ch_", ""))
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
    elif data == "manual_payment":
        payment_card = (await get_setting('payment_card')) or PAYMENT_CARD or "Kiritilmagan"
        payment_owner = (await get_setting('payment_owner')) or PAYMENT_OWNER or "Kiritilmagan"
        note = (await get_setting('payment_note')) or "To'lovdan keyin screenshot yuboriladi va admin tasdiqlaydi."
        await safe_edit_text(
            query,
            f"💳 <b>Oddiy to'lov tizimi</b>\n\n💳 Karta: <code>{payment_card}</code>\n👤 Egasi: <b>{payment_owner}</b>\n\n{note}",
            parse_mode="HTML",
            reply_markup=back_keyboard("payment_settings")
        )
    elif data == "auto_payment":
        await safe_edit_text(
            query,
            "⚡ Avtomatik to'lov hozircha yo'q. Manual premium oqimi tayyor.",
            reply_markup=back_keyboard("payment_settings"),
            parse_mode=None
        )
    elif data == "premium_settings":
        await adm.premium_settings_menu(update, context)
    elif data == "premium_requests":
        await show_pending_requests(update, context)
    elif data == "toggle_premium":
        await adm.toggle_premium(update, context)
    elif data == "premium_users":
        await adm.show_premium_users(update, context)
    elif data == "premium_tariffs":
        await tr_h.show_tariffs(update, context)
    elif data == "tariff_add":
        await tr_h.start_add_tariff(update, context)
    elif data.startswith("tariff_edit_name_"):
        await tr_h.edit_tariff_field(update, context, int(data.replace("tariff_edit_name_", "")), "name")
    elif data.startswith("tariff_edit_days_"):
        await tr_h.edit_tariff_field(update, context, int(data.replace("tariff_edit_days_", "")), "duration_days")
    elif data.startswith("tariff_edit_price_"):
        await tr_h.edit_tariff_field(update, context, int(data.replace("tariff_edit_price_", "")), "price")
    elif data.startswith("tariff_toggle_"):
        await tr_h.toggle_tariff(update, context, int(data.replace("tariff_toggle_", "")))
    elif data.startswith("tariff_del_"):
        await tr_h.delete_tariff(update, context, int(data.replace("tariff_del_", "")))
    elif data.startswith("tariff_"):
        await tr_h.show_tariff_detail(update, context, int(data.replace("tariff_", "")))
    elif data == "give_premium":
        await adm.start_give_premium(update, context)
    else:
        await query.answer("Noma'lum amal", show_alert=False)
