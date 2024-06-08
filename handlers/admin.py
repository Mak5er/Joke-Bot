import asyncio
import logging
import os
import platform
from io import BytesIO

import cpuinfo
import pandas as pd
import psutil
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from filters import IsBotAdmin
from aiogram.types import BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State

from keyboards import inline_keyboards as kb
from main import bot, _, send_analytics, i18n
from messages import bot_messages as bm
from services import DataBase

db = DataBase()

admin_router = Router()


class Mailing(StatesGroup):
    send_to_all_message = State()


class Admin(StatesGroup):
    add_joke = State()
    control_user = State()
    ban_reason = State()
    feedback_answer = State()
    write_message = State()


@admin_router.message(Command("admin"), IsBotAdmin())
async def admin(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")

    if message.chat.type == 'private':
        user_id = message.from_user.id

        table_name = f"jokes_uk"

        logging.info(f"User action: /admin (User ID: {user_id})")

        user_count = await db.user_count()
        active_user_count = await db.active_user_count()
        inactive_user_count = await db.inactive_user_count()
        joke_count = await db.joke_count(table_name)
        sent_count = await db.sent_count()

        await message.answer(bm.admin_panel(
            user_count, active_user_count, inactive_user_count, joke_count, sent_count),
            reply_markup=kb.admin_keyboard(), parse_mode='HTML')
    else:
        await message.answer(bm.not_groups())


@admin_router.message(Command('system_info'), IsBotAdmin())
async def system_info(message: types.Message):
    clock_message = await message.reply('⏳')
    system_specs = {
        'operating_system': platform.system(),
        'os_version': platform.version(),
        'machine_name': platform.node(),
        'processor_architecture': platform.machine(),
        'processor_model': cpuinfo.get_cpu_info()['brand_raw'],
        'physical_cores': psutil.cpu_count(logical=False),
        'logical_cores': psutil.cpu_count(logical=True),
        'total_memory': psutil.virtual_memory().total / (1024 * 1024),
        'available_memory': psutil.virtual_memory().available / (1024 * 1024),
        'memory_usage': psutil.virtual_memory().percent
    }
    formatted_system_info = bm.get_formatted_system_info(system_specs)
    await bot.delete_message(message.chat.id, clock_message.message_id)
    await message.reply(formatted_system_info)


@admin_router.callback_query(F.data == 'delete_log')
async def del_log(call: types.CallbackQuery):
    await bot.send_chat_action(call.message.chat.id, "typing")
    logging.shutdown()
    open('log/bot_log.log', 'w').close()
    await call.message.reply(bm.log_deleted())
    await call.answer()


@admin_router.callback_query(F.data == 'download_log')
async def download_log_handler(call: types.CallbackQuery):
    await bot.send_chat_action(call.message.chat.id, "typing")

    log_file = 'log/bot_log.log'
    user_id = call.from_user.id

    await call.answer()

    with open(log_file, 'rb') as file:
        await call.message.answer_document(BufferedInputFile(file.read(), filename="bot_log.log"))
        logging.info(f"User action: Downloaded log (User ID: {user_id})")
        return


@admin_router.callback_query(F.data == 'send_to_all')
async def send_to_all_callback(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(chat_id=call.message.chat.id,
                           text=bm.mailing_message(),
                           reply_markup=kb.cancel_keyboard())
    await state.set_state(Mailing.send_to_all_message)
    await call.answer()


@admin_router.message(Mailing.send_to_all_message)
async def send_to_all_message(message: types.Message, state: FSMContext):
    sender_id = message.from_user.id
    if message.text == _("↩️Cancel"):
        await bot.send_message(message.chat.id, bm.canceled(), reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return

    else:
        await state.clear()

        await bot.send_message(chat_id=message.chat.id,
                               text=bm.start_mailing(i18n, await db.get_language(message.from_user.id)),
                               reply_markup=types.ReplyKeyboardRemove())

        users = await db.all_users()
        for user in users:
            try:
                await bot.forward_message(chat_id=user[0],
                                          from_chat_id=sender_id,
                                          message_id=message.message_id)
                logging.info(f"Sent message to user {user[0]}: {message.text}")

                user_status = await db.status(user[0])

                if user_status == "inactive":
                    await db.set_active(user[0])

                await asyncio.sleep(
                    0.05
                )

            except Exception as e:
                logging.error(f"Error sending message to user {user[0]}: {str(e)}")

                if str(e) == "Forbidden: bots can't send messages to bots":
                    await db.delete_user(user[0])

                if "blocked" or "Chat not found" in str(e):
                    await db.set_inactive(user[0])
                continue

        await bot.send_message(chat_id=message.chat.id,
                               text=bm.finish_mailing(i18n, await db.get_language(message.from_user.id)),
                               reply_markup=types.ReplyKeyboardRemove())
        return


@admin_router.callback_query(F.data == 'add_joke')
async def add_joke_handler(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(chat_id=call.message.chat.id,
                           text=bm.new_joke(),
                           reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.add_joke)
    await call.answer()


@admin_router.message(Admin.add_joke)
async def save_joke(message: types.Message, state: FSMContext):
    joke_text = message.text
    if joke_text == _("↩️Cancel"):
        await bot.send_message(chat_id=message.chat.id,
                               text=bm.canceled(),
                               reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    else:
        table_name = f"jokes_uk"
        await db.add_joke(joke_text, table_name)

        await message.reply(bm.joke_added(),
                            reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        user_id = message.from_user.id
        logging.info(
            f"User action: Add joke (User ID: {user_id}), (Joke text: {message.text})"
        )


@admin_router.callback_query(F.data == 'daily_joke')
async def send_daily_joke(call: types.CallbackQuery):
    await call.answer()
    from handlers.user import daily_joke
    await daily_joke()


@admin_router.callback_query(F.data == 'control_user')
async def control_user_callback(call: types.CallbackQuery):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await call.message.answer(text=bm.search_user_by(), reply_markup=kb.return_search_keyboard())
    await call.answer()


@admin_router.callback_query(F.data.startswith("search_"))
async def search_user_by(call: types.CallbackQuery, state: FSMContext):
    search = call.data.split('_')[1]
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await call.message.answer(text=bm.type_user(search), reply_markup=kb.cancel_keyboard())

    await state.set_state(Admin.control_user)
    await state.update_data(search=search)
    await call.answer()


@admin_router.message(Admin.control_user)
async def control_user(message: types.Message, state: FSMContext):
    answer = message.text
    answer = answer.replace("@", "")
    answer = answer.replace("https://t.me/", "")
    data = await state.get_data()
    search = data.get("search")

    if message.text == _("↩️Cancel"):
        await bot.send_message(message.chat.id, bm.action_canceled(),
                               reply_markup=ReplyKeyboardRemove())
        await state.clear()
        await admin(message)
        return

    else:
        await bot.send_chat_action(message.chat.id, "typing")

        clock = await bot.send_message(message.chat.id, '⏳', reply_markup=ReplyKeyboardRemove())

        await asyncio.sleep(2)

        await bot.delete_message(message.chat.id, clock.message_id)

        user = None

        if search == "id":
            user = await db.get_user_info(answer)

        elif search == "username":
            user = await db.get_user_info_username(answer)

        result = user

        if result is not None:
            user_name = None
            user_username = None
            status = None
            user_id = None

            if search == "id":
                user_name, user_username, status = result
                user_id = answer

            elif search == "username":
                user_name, user_id, status = result
                user_username = answer

            builder = InlineKeyboardBuilder()

            go_to_chat = InlineKeyboardButton(text=_("Enter in Conversation"), url=f"tg://user?id={user_id}")
            write_user = InlineKeyboardButton(text=_('Write as a bot'), callback_data=f"write_{user_id}")
            ban_button = InlineKeyboardButton(text=_("❌Ban"), callback_data=f"ban_{user_id}")
            unban_button = InlineKeyboardButton(text=_("✅Unban"), callback_data=f"unban_{user_id}")
            back_button = InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")
            builder.row(go_to_chat, write_user)

            if user_username == "":
                user_username = "None"
            else:
                user_username = f"@{user_username}"

            user_photo = await bot.get_user_profile_photos(user_id, limit=1)

            if status == 'active':
                builder.row(ban_button)

            elif status == 'ban':
                builder.row(unban_button)

            builder.row(back_button)

            if user_photo.total_count > 0:
                await message.reply_photo(user_photo.photos[0][-1].file_id,
                                          caption=bm.return_user_info(user_name, user_id, user_username, status),
                                          reply_markup=builder.as_markup(), parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id, bm.return_user_info(user_name, user_id, user_username, status),
                                       reply_markup=builder.as_markup(), parse_mode="HTML")
            logging.info(f"Control user: {user_id}")

        else:
            await bot.send_message(message.chat.id, _("User not found!"))

        await state.clear()


@admin_router.callback_query(F.data.startswith("ban_"))
async def message_handler(call: types.CallbackQuery, state: FSMContext):
    banned_user_id = call.data.split("_")[1]

    await call.message.delete()
    await call.message.answer(_('Enter ban reason:'), reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.ban_reason)
    await state.update_data(banned_user_id=banned_user_id)
    await call.answer()


@admin_router.message(Admin.ban_reason)
async def control_user(message: types.Message, state: FSMContext):
    reason = message.text
    data = await state.get_data()
    banned_user_id = data.get("banned_user_id")

    if message.text == _("↩️Cancel"):
        await bot.send_message(message.chat.id, bm.action_canceled(),
                               reply_markup=ReplyKeyboardRemove())
        await state.clear()
        await admin(message)
        return

    await db.ban_user(banned_user_id)

    await state.clear()

    await bot.send_message(chat_id=banned_user_id,
                           text=bm.ban_message(reason),
                           reply_markup=ReplyKeyboardRemove())

    ban_message = await message.answer(bm.successful_ban(banned_user_id),
                                       reply_markup=ReplyKeyboardRemove())

    await bot.delete_message(message.chat.id, ban_message.message_id)

    await message.answer(bm.successful_ban(banned_user_id), reply_markup=kb.return_back_to_admin_keyboard())

    logging.info(f"Banned user: {banned_user_id} Reason: {reason}")


@admin_router.callback_query(F.data.startswith("unban_"))
async def message_handler(call: types.CallbackQuery):
    unbanned_user_id = call.data.split("_")[1]

    await db.set_active(unbanned_user_id)

    await bot.send_message(chat_id=unbanned_user_id,
                           text=bm.unban_message())

    await call.message.delete()

    await call.message.answer(bm.successful_unban(unbanned_user_id),
                              reply_markup=kb.return_back_to_admin_keyboard())

    await call.answer()

    logging.info(f"Unbanned user: {unbanned_user_id}")


@admin_router.message(Command('info'), IsBotAdmin())
async def info(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    table_name = f"jokes_uk"

    logging.info(f"User action: /info (User ID: {user_id})")

    joke_sent = await db.joke_sent(user_id)
    joke_count = await db.joke_count(table_name)
    sent_count = await db.sent_count()
    refs_count = await db.refs_count(user_id)
    ref_url = f't.me/{(await bot.get_me()).username}?start=ref{user_id}'

    username = message.from_user.first_name

    await message.reply(
        bm.admin_info(username, joke_sent, joke_count, sent_count, refs_count, ref_url),
        reply_markup=kb.return_feedback_button(),
        parse_mode='HTML')

    await send_analytics(user_id=message.from_user.id, user_lang_code=message.from_user.language_code,
                         action_name='info')


@admin_router.message(Command('get_users'), IsBotAdmin())
async def export_users_data(message: types.Message):
    clock = await bot.send_message(message.chat.id, '⏳', reply_markup=ReplyKeyboardRemove())
    users = await db.all_users()

    for user in users:
        chat_id = user[0]

        try:
            user = await bot.get_chat(chat_id)
        except Exception as e:
            print(e)
            if str(e) == 'Chat not found':
                # Handle ChatNotFound exception
                await db.delete_user(chat_id)

            # Handle other exceptions as needed
            print(f"An error occurred: {str(e)} Chat ID: {chat_id}")
            continue

        username = user.username if user.username else ""
        full_name = user.full_name if user.full_name else ""
        await db.user_update_name(chat_id, full_name, username)

    await asyncio.sleep(2)

    # Виконуємо запит для отримання всіх даних з таблиці users

    users_data = await db.get_all_users_info()

    # Створюємо DataFrame з даними користувачів
    df = pd.DataFrame(users_data, columns=['user_id', 'chat_type', 'user_name', 'user_username', 'language', 'status',
                                           'referrer_id'])

    # Створюємо Excel-файл з даними
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)

    # Збереження файлу на комп'ютеріs
    file_path = 'users_data.xlsx'
    with open(file_path, 'wb') as file:
        file.write(excel_file.getvalue())

    await bot.delete_message(message.chat.id, clock.message_id)

    # Відправляємо Excel-файл у вашому Telegram-боті
    with open(file_path, 'rb') as file:
        await message.answer_document(BufferedInputFile(file.read(), filename=file_path))

    logging.info(f"Getting info about user")

    # Видаляємо файл з комп'ютера
    os.remove(file_path)


@admin_router.callback_query(F.data == 'back_to_admin')
async def back_to_admin(call: types.CallbackQuery):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_chat_action(call.message.chat.id, "typing")

    user_id = call.from_user.id

    table_name = f"jokes_uk"

    logging.info(f"User action: /admin (User ID: {user_id})")

    user_count = await db.user_count()
    active_user_count = await db.active_user_count()
    inactive_user_count = await db.inactive_user_count()
    joke_count = await db.joke_count(table_name)
    sent_count = await db.sent_count()

    await call.message.answer(bm.admin_panel(user_count, active_user_count, inactive_user_count, joke_count,
                                             sent_count),
                              reply_markup=kb.admin_keyboard(),
                              parse_mode='HTML')


@admin_router.callback_query(F.data.startswith("answer_"))
async def answer_feedback_handler(call: types.CallbackQuery, state: FSMContext):
    message_id = call.data.split("_")[1]
    chat_id = call.data.split("_")[2]
    await call.message.delete_reply_markup()
    await call.message.answer(_('Please type your answer:'), reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.feedback_answer)
    await state.update_data(message_id=message_id, chat_id=chat_id)


@admin_router.message(Admin.feedback_answer)
async def answer_feedback(message: types.Message, state: FSMContext):
    answer = message.text

    if answer == _("↩️Cancel"):
        await bot.send_message(message.chat.id, bm.action_canceled(), reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    data = await state.get_data()
    message_id = data.get('message_id')
    chat_id = data.get('chat_id')
    await state.clear()

    try:
        await bot.send_message(chat_id=chat_id,
                               text=_(
                                   'Your message <b>{message_id}</b> was seen!\n<b>Answer:</b> <code>{answer}</code>').format(
                                   message_id=message_id, answer=answer))
        await message.reply(_('Your answer sent!'), reply_markup=ReplyKeyboardRemove())
        logging.info(f"Sent answer for feedback to user {chat_id}: {answer}")

    except Exception as e:
        await message.reply(_("Something went wrong, see log for more information!"),
                            reply_markup=kb.return_back_to_admin_keyboard())
        logging.error(f"Error sending message to user {chat_id}: {str(e)}")


@admin_router.callback_query(F.data.startswith("write_"))
async def write_message_handler(call: types.CallbackQuery, state: FSMContext):
    chat_id = call.data.split("_")[1]
    await call.message.delete_reply_markup()
    await call.message.delete()
    await call.message.answer(_('Please type message:'), reply_markup=kb.cancel_keyboard())
    await state.set_state(Admin.write_message)
    await state.update_data(chat_id=chat_id)


@admin_router.message(Admin.write_message)
async def write_message(message: types.Message, state: FSMContext):
    answer = message.text

    if answer == _("↩️Cancel"):
        await bot.send_message(message.chat.id, bm.action_canceled(), reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    data = await state.get_data()
    chat_id = data.get('chat_id')
    await state.clear()

    try:
        await bot.send_message(chat_id=chat_id,
                               text=answer)
        message_sent = await message.reply(bm.your_message_sent(), reply_markup=ReplyKeyboardRemove())

        await bot.delete_message(message.chat.id, message_sent.message_id)

        await message.answer(bm.your_message_sent(), reply_markup=kb.return_back_to_admin_keyboard())

        logging.info(f"Sent message as bot to user {chat_id}: {answer}")

    except Exception as e:
        await message.reply(bm.something_went_wrong(),
                            reply_markup=kb.return_back_to_admin_keyboard())
        logging.error(f"Error sending message to user {chat_id}: {str(e)}")


@admin_router.message(Command('ideas'), IsBotAdmin())
async def return_ideas(message: types.Message):
    ideas = await db.get_ideas()

    if ideas:
        response = _("<b>Ideas for you:</b>\n\n")
        builder = InlineKeyboardBuilder()
        i = 1

        for idea in ideas:
            idea_text = idea[1][:30] + "..." if len(idea[1]) > 30 else idea[1]
            response += f"#{i} - <i>{idea_text}</i>\n"
            i += 1

            idea_text_button = types.InlineKeyboardButton(text=f"{idea_text}", callback_data=f"manage_idea:{idea[0]}")
            builder.row(idea_text_button)

        add_button = types.InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")
        builder.add(add_button)
        await bot.send_message(chat_id=message.chat.id, text=response, reply_markup=builder.as_markup(),
                               parse_mode='HTML')
    else:
        builder = InlineKeyboardBuilder()
        button = types.InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")
        builder.add(button)

        await bot.send_message(chat_id=message.chat.id, text=bm.any_ideas(), reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith('manage_idea:'))
async def manage_idea_callback(call: types.CallbackQuery):
    idea_id = int(call.data.split(':')[1])

    idea = await db.get_idea(idea_id)

    if idea:
        builder = InlineKeyboardBuilder()
        delete_button = types.InlineKeyboardButton(text=_("❌Delete"), callback_data=f"delete_idea:{idea_id}")
        back_button = types.InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_list")
        builder.row(delete_button)
        builder.row(back_button)

        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=idea[0],
                                    reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith('delete_idea:'))
async def delete_idea_callback(call: types.CallbackQuery):
    idea_id = int(call.data.split(':')[1])
    message = call.message

    await db.delete_idea(idea_id)

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text=bm.idea_deleted())
    await return_ideas(message)
    await bot.answer_callback_query(call.id)


@admin_router.callback_query(F.data == 'back_to_list')
async def back_to_list_callback(call: types.CallbackQuery):
    message = call.message

    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await return_ideas(message)
    await bot.answer_callback_query(call.id)
