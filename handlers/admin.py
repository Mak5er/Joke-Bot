import asyncio
import logging
import platform
from io import BytesIO
from pathlib import Path

import cpuinfo
import pandas as pd
import psutil
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import bot, get_bot_username, i18n, send_analytics
from bot_utils import is_cancel_action, is_unavailable_chat_error
from config import ADMINS_UID, DEFAULT_LOCALE, JOKES_TABLE
from filters import IsBotAdmin
from keyboards import inline_keyboards as kb
from messages import bot_messages as bm
from services import database as db

logger = logging.getLogger(__name__)
admin_router = Router()
admin_router.message.filter(IsBotAdmin())
admin_router.callback_query.filter(F.from_user.id.in_(ADMINS_UID))


class Mailing(StatesGroup):
    send_to_all_message = State()


class Admin(StatesGroup):
    add_joke = State()
    control_user = State()
    ban_reason = State()
    feedback_answer = State()
    write_message = State()


async def send_admin_panel(message: types.Message) -> None:
    user_count, active_user_count, inactive_user_count, joke_count, sent_count = await asyncio.gather(
        db.user_count(),
        db.active_user_count(),
        db.inactive_user_count(),
        db.joke_count(JOKES_TABLE),
        db.sent_count(),
    )
    await message.answer(
        bm.admin_panel(user_count, active_user_count, inactive_user_count, joke_count, sent_count),
        reply_markup=kb.admin_keyboard(),
    )


@admin_router.message(Command("admin"))
async def admin(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    if message.chat.type != "private":
        await message.answer(bm.not_groups())
        return

    logger.info("User action: /admin (user_id=%s)", message.from_user.id)
    await send_admin_panel(message)


@admin_router.message(Command("system_info"))
async def system_info(message: types.Message):
    clock_message = await message.reply("...")
    system_specs = {
        "operating_system": platform.system(),
        "os_version": platform.version(),
        "machine_name": platform.node(),
        "processor_architecture": platform.machine(),
        "processor_model": cpuinfo.get_cpu_info()["brand_raw"],
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "total_memory": psutil.virtual_memory().total / (1024 * 1024),
        "available_memory": psutil.virtual_memory().available / (1024 * 1024),
        "memory_usage": psutil.virtual_memory().percent,
    }
    await bot.delete_message(message.chat.id, clock_message.message_id)
    await message.reply(bm.get_formatted_system_info(system_specs))


@admin_router.callback_query(F.data == "delete_log")
async def del_log(call: types.CallbackQuery):
    await bot.send_chat_action(call.message.chat.id, "typing")
    logging.shutdown()
    Path("log/bot_log.log").write_text("", encoding="utf-8")
    await call.message.reply(bm.log_deleted())
    await call.answer()


@admin_router.callback_query(F.data == "download_log")
async def download_log_handler(call: types.CallbackQuery):
    await bot.send_chat_action(call.message.chat.id, "typing")
    log_file = Path("log/bot_log.log")
    if log_file.exists():
        await call.message.answer_document(BufferedInputFile(log_file.read_bytes(), filename="bot_log.log"))
        logger.info("Downloaded log (user_id=%s)", call.from_user.id)
    await call.answer()


@admin_router.callback_query(F.data == "send_to_all")
async def send_to_all_callback(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(call.message.chat.id, bm.mailing_message(), reply_markup=kb.cancel_keyboard())
    await state.set_state(Mailing.send_to_all_message)
    await call.answer()


@admin_router.message(Mailing.send_to_all_message)
async def send_to_all_message(message: types.Message, state: FSMContext):
    if is_cancel_action(message.text):
        await bot.send_message(message.chat.id, bm.canceled(), reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return

    await state.clear()
    user_locale = await db.get_language(message.from_user.id) or DEFAULT_LOCALE
    await bot.send_message(
        message.chat.id,
        bm.start_mailing(i18n, user_locale),
        reply_markup=types.ReplyKeyboardRemove(),
    )

    users = await db.all_users()
    for user in users:
        chat_id = user[0]
        try:
            await bot.forward_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=message.message_id)
            logger.info("Sent mailing message to user %s", chat_id)

            user_status = await db.status(chat_id)
            if user_status == "inactive":
                await db.set_active(chat_id)

            await asyncio.sleep(0.05)
        except Exception as error:
            logger.error("Error sending mailing message to user %s: %s", chat_id, error)
            if is_unavailable_chat_error(error):
                await db.set_inactive(chat_id)

    await bot.send_message(
        message.chat.id,
        bm.finish_mailing(i18n, user_locale),
        reply_markup=types.ReplyKeyboardRemove(),
    )


@admin_router.callback_query(F.data == "add_joke")
async def add_joke_handler(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(call.message.chat.id, bm.new_joke(), reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.add_joke)
    await call.answer()


@admin_router.message(Admin.add_joke)
async def save_joke(message: types.Message, state: FSMContext):
    if is_cancel_action(message.text):
        await bot.send_message(message.chat.id, bm.canceled(), reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return

    await db.add_joke(message.text, JOKES_TABLE)
    await message.reply(bm.joke_added(), reply_markup=types.ReplyKeyboardRemove())
    await state.clear()
    logger.info("Added a joke (user_id=%s)", message.from_user.id)


@admin_router.callback_query(F.data == "daily_joke")
async def send_daily_joke(call: types.CallbackQuery):
    from handlers.user import daily_joke

    await call.answer()
    await daily_joke()


@admin_router.callback_query(F.data == "control_user")
async def control_user_callback(call: types.CallbackQuery):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await call.message.answer(text=bm.search_user_by(), reply_markup=kb.return_search_keyboard())
    await call.answer()


@admin_router.callback_query(F.data.startswith("search_"))
async def search_user_by(call: types.CallbackQuery, state: FSMContext):
    search = call.data.split("_", maxsplit=1)[1]
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await call.message.answer(text=bm.type_user(search), reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.control_user)
    await state.update_data(search=search)
    await call.answer()


@admin_router.message(Admin.control_user)
async def control_user(message: types.Message, state: FSMContext):
    answer = (message.text or "").replace("@", "").replace("https://t.me/", "").strip()
    if is_cancel_action(message.text):
        await bot.send_message(message.chat.id, bm.action_canceled(), reply_markup=ReplyKeyboardRemove())
        await state.clear()
        await send_admin_panel(message)
        return

    data = await state.get_data()
    search = data.get("search")
    await bot.send_chat_action(message.chat.id, "typing")

    user = None
    if search == "id" and answer.lstrip("-").isdigit():
        user = await db.get_user_info(int(answer))
    elif search == "username":
        user = await db.get_user_info_username(answer)

    if user is None:
        await bot.send_message(message.chat.id, _("User not found!"))
        await state.clear()
        return

    if search == "id":
        user_name, user_username, status = user
        user_id = int(answer)
    else:
        user_name, user_id, status = user
        user_username = answer

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=_("Enter in Conversation"), url=f"tg://user?id={user_id}"),
        InlineKeyboardButton(text=_("Write as a bot"), callback_data=f"write_{user_id}"),
    )

    if status == "active":
        builder.row(InlineKeyboardButton(text=_("Ban"), callback_data=f"ban_{user_id}"))
    elif status == "ban":
        builder.row(InlineKeyboardButton(text=_("Unban"), callback_data=f"unban_{user_id}"))

    builder.row(InlineKeyboardButton(text=_("Back"), callback_data="back_to_admin"))

    username_text = f"@{user_username}" if user_username else "None"
    user_photo = await bot.get_user_profile_photos(user_id, limit=1)
    response_text = bm.return_user_info(user_name, user_id, username_text, status)

    if user_photo.total_count > 0:
        await message.reply_photo(
            user_photo.photos[0][-1].file_id,
            caption=response_text,
            reply_markup=builder.as_markup(),
        )
    else:
        await bot.send_message(message.chat.id, response_text, reply_markup=builder.as_markup())

    logger.info("Control user %s", user_id)
    await state.clear()


@admin_router.callback_query(F.data.startswith("ban_"))
async def ban_user_request(call: types.CallbackQuery, state: FSMContext):
    banned_user_id = int(call.data.split("_", maxsplit=1)[1])
    await call.message.delete()
    await call.message.answer(_("Enter ban reason:"), reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.ban_reason)
    await state.update_data(banned_user_id=banned_user_id)
    await call.answer()


@admin_router.message(Admin.ban_reason)
async def ban_user(message: types.Message, state: FSMContext):
    if is_cancel_action(message.text):
        await bot.send_message(message.chat.id, bm.action_canceled(), reply_markup=ReplyKeyboardRemove())
        await state.clear()
        await send_admin_panel(message)
        return

    data = await state.get_data()
    banned_user_id = data.get("banned_user_id")
    await db.ban_user(banned_user_id)
    await state.clear()

    try:
        await bot.send_message(chat_id=banned_user_id, text=bm.ban_message(message.text), reply_markup=ReplyKeyboardRemove())
    except Exception:
        logger.warning("Failed to notify banned user %s", banned_user_id, exc_info=True)

    await message.answer(bm.successful_ban(banned_user_id), reply_markup=kb.return_back_to_admin_keyboard())
    logger.info("Banned user %s", banned_user_id)


@admin_router.callback_query(F.data.startswith("unban_"))
async def unban_user(call: types.CallbackQuery):
    unbanned_user_id = int(call.data.split("_", maxsplit=1)[1])
    await db.set_active(unbanned_user_id)

    try:
        await bot.send_message(chat_id=unbanned_user_id, text=bm.unban_message())
    except Exception:
        logger.warning("Failed to notify unbanned user %s", unbanned_user_id, exc_info=True)

    await call.message.delete()
    await call.message.answer(bm.successful_unban(unbanned_user_id), reply_markup=kb.return_back_to_admin_keyboard())
    await call.answer()
    logger.info("Unbanned user %s", unbanned_user_id)


@admin_router.message(Command("info"))
async def info(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id
    joke_sent, joke_count, sent_count, refs_count = await asyncio.gather(
        db.joke_sent(user_id),
        db.joke_count(JOKES_TABLE),
        db.sent_count(),
        db.refs_count(user_id),
    )
    ref_url = f"t.me/{await get_bot_username()}?start=ref{user_id}"

    await message.reply(
        bm.admin_info(message.from_user.first_name, joke_sent, joke_count, sent_count, refs_count, ref_url),
        reply_markup=kb.return_feedback_button(),
    )
    await send_analytics(user_id=user_id, user_lang_code=message.from_user.language_code, action_name="info")


@admin_router.message(Command("get_users"))
async def export_users_data(message: types.Message):
    clock = await bot.send_message(message.chat.id, "...", reply_markup=ReplyKeyboardRemove())
    users = await db.all_users()

    for user in users:
        chat_id = user[0]
        try:
            chat = await bot.get_chat(chat_id)
        except Exception as error:
            logger.warning("Failed to fetch chat %s: %s", chat_id, error)
            if is_unavailable_chat_error(error):
                await db.set_inactive(chat_id)
            continue

        username = chat.username or ""
        full_name = chat.full_name or ""
        await db.user_update_name(chat_id, full_name, username)

    users_data = await db.get_all_users_info()
    dataframe = pd.DataFrame(
        users_data,
        columns=["user_id", "chat_type", "user_name", "user_username", "language", "status", "referrer_id"],
    )

    excel_buffer = BytesIO()
    dataframe.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    await bot.delete_message(message.chat.id, clock.message_id)
    await message.answer_document(BufferedInputFile(excel_buffer.getvalue(), filename="users_data.xlsx"))
    logger.info("Exported users data")


@admin_router.callback_query(F.data == "back_to_admin")
async def back_to_admin(call: types.CallbackQuery):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_chat_action(call.message.chat.id, "typing")
    await send_admin_panel(call.message)
    await call.answer()


@admin_router.callback_query(F.data.startswith("answer_"))
async def answer_feedback_handler(call: types.CallbackQuery, state: FSMContext):
    action, message_id, chat_id = call.data.split("_", maxsplit=2)
    await call.message.delete_reply_markup()
    await call.message.answer(_("Please type your answer:"), reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.feedback_answer)
    await state.update_data(message_id=message_id, chat_id=int(chat_id))
    await call.answer()


@admin_router.message(Admin.feedback_answer)
async def answer_feedback(message: types.Message, state: FSMContext):
    if is_cancel_action(message.text):
        await bot.send_message(message.chat.id, bm.action_canceled(), reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    data = await state.get_data()
    chat_id = data.get("chat_id")
    message_id = data.get("message_id")
    await state.clear()

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=_("Your message <b>{message_id}</b> was seen!\n<b>Answer:</b> <code>{answer}</code>").format(
                message_id=message_id,
                answer=message.text,
            ),
        )
        await message.reply(_("Your answer sent!"), reply_markup=ReplyKeyboardRemove())
        logger.info("Sent answer for feedback to user %s", chat_id)
    except Exception as error:
        await message.reply(_("Something went wrong, see log for more information!"), reply_markup=kb.return_back_to_admin_keyboard())
        logger.error("Error sending feedback answer to user %s: %s", chat_id, error)


@admin_router.callback_query(F.data.startswith("write_"))
async def write_message_handler(call: types.CallbackQuery, state: FSMContext):
    chat_id = int(call.data.split("_", maxsplit=1)[1])
    await call.message.delete_reply_markup()
    await call.message.delete()
    await call.message.answer(_("Please type message:"), reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.write_message)
    await state.update_data(chat_id=chat_id)
    await call.answer()


@admin_router.message(Admin.write_message)
async def write_message(message: types.Message, state: FSMContext):
    if is_cancel_action(message.text):
        await bot.send_message(message.chat.id, bm.action_canceled(), reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    data = await state.get_data()
    chat_id = data.get("chat_id")
    await state.clear()

    try:
        await bot.send_message(chat_id=chat_id, text=message.text)
        await message.answer(bm.your_message_sent(), reply_markup=kb.return_back_to_admin_keyboard())
        logger.info("Sent message as bot to user %s", chat_id)
    except Exception as error:
        await message.reply(bm.something_went_wrong(), reply_markup=kb.return_back_to_admin_keyboard())
        logger.error("Error sending direct bot message to user %s: %s", chat_id, error)


@admin_router.message(Command("ideas"))
async def return_ideas(message: types.Message):
    ideas = await db.get_ideas()
    builder = InlineKeyboardBuilder()

    if not ideas:
        builder.row(types.InlineKeyboardButton(text=_("Back"), callback_data="back_to_admin"))
        await bot.send_message(chat_id=message.chat.id, text=bm.any_ideas(), reply_markup=builder.as_markup())
        return

    response = _("<b>Ideas for you:</b>\n\n")
    for index, idea in enumerate(ideas, start=1):
        idea_text = idea[1][:30] + "..." if len(idea[1]) > 30 else idea[1]
        response += f"#{index} - <i>{idea_text}</i>\n"
        builder.row(types.InlineKeyboardButton(text=idea_text, callback_data=f"manage_idea:{idea[0]}"))

    builder.row(types.InlineKeyboardButton(text=_("Back"), callback_data="back_to_admin"))
    await bot.send_message(chat_id=message.chat.id, text=response, reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith("manage_idea:"))
async def manage_idea_callback(call: types.CallbackQuery):
    idea_id = int(call.data.split(":", maxsplit=1)[1])
    idea = await db.get_idea(idea_id)
    if not idea:
        await call.answer(bm.any_ideas(), show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=_("Delete"), callback_data=f"delete_idea:{idea_id}"))
    builder.row(types.InlineKeyboardButton(text=_("Back"), callback_data="back_to_list"))

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=idea[0],
        reply_markup=builder.as_markup(),
    )
    await call.answer()


@admin_router.callback_query(F.data.startswith("delete_idea:"))
async def delete_idea_callback(call: types.CallbackQuery):
    idea_id = int(call.data.split(":", maxsplit=1)[1])
    await db.delete_idea(idea_id)
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=bm.idea_deleted())
    await return_ideas(call.message)
    await call.answer()


@admin_router.callback_query(F.data == "back_to_list")
async def back_to_list_callback(call: types.CallbackQuery):
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await return_ideas(call.message)
    await call.answer()
