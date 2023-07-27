import asyncio
import logging
import os
from io import BytesIO

import pandas as pd
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

import config
from keyboards import inline_keyboards as kb
from log.logger import custom_formatter
from main import dp, bot, _
from messages import bot_messages
from messages import bot_messages as bm
from middlewares.throttling_middleware import rate_limit
from services import DataBase

storage = MemoryStorage()

db = DataBase('services/jokes.db')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/bot_log.log")
handler.setFormatter(custom_formatter)

logger.addHandler(handler)

admin_id = config.admin_id


@dp.message_handler(commands=['admin'])
@rate_limit(2)
async def admin(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    if message.chat.type == 'private':
        user_id = message.from_user.id
        language = await db.get_language(user_id)

        table_name = f"jokes_{language}"

        logging.info(f"User action: /admin (User ID: {user_id})")

        user_count = await db.user_count()
        joke_count = await db.joke_count(table_name)
        sent_count = await db.sent_count()

        await message.answer(bot_messages.admin_panel(
            user_count, joke_count, sent_count),
            reply_markup=kb.admin_keyboard(), parse_mode='Markdown')
    else:
        await message.answer(bot_messages.not_groups())


@dp.message_handler(user_id=admin_id, commands=['del_log'])
@rate_limit(10)
async def del_log(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")
    logging.shutdown()
    open('log/bot_log.log', 'w').close()
    await message.reply(bot_messages.log_deleted())


@dp.message_handler(user_id=admin_id, commands=['download_db'])
@rate_limit(10)
async def download_db(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")
    user_id = message.from_user.id
    db_file = 'services/jokes.db'
    with open(db_file, 'rb') as file:
        await bot.send_document(message.chat.id, file)
        logging.info(
            f"User action: Downloaded db (User ID: {user_id})")


@dp.callback_query_handler(lambda call: call.data == 'download_log')
async def download_log_handler(call: types.CallbackQuery):
    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    log_file = 'log/bot_log.log'
    user_id = call.from_user.id

    with open(log_file, 'rb') as file:
        await bot.send_document(call.message.chat.id, file)
        logging.info(f"User action: Downloaded log (User ID: {user_id})")


@dp.callback_query_handler(lambda call: call.data == 'send_to_all')
async def send_to_all_callback(call: types.CallbackQuery):
    await bot.send_message(chat_id=call.message.chat.id,
                           text=bot_messages.mailing_message(),
                           reply_markup=kb.cancel_keyboard())
    await dp.current_state().set_state("send_to_all_message")


@dp.message_handler(user_id=admin_id, state="send_to_all_message")
async def send_to_all_message(message: types.Message, state: FSMContext):
    sender_id = message.from_user.id
    if message.text == _("↩️Cancel"):
        await bot.send_message(message.chat.id, bot_messages.canceled(), reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return
    else:
        await dp.bot.send_chat_action(message.chat.id, "typing")

        users = await db.all_users()

        for user in users:
            try:
                await bot.copy_message(chat_id=user[0],
                                       from_chat_id=sender_id,
                                       message_id=message.message_id,
                                       parse_mode="Markdown")
                logging.info(f"Sent message to user {user[0]}: {message.text}")
            except Exception as e:
                logging.error(
                    f"Error sending message to user {user[0]}: {str(e)}")
                continue
        await bot.send_message(chat_id=message.chat.id,
                               text=bot_messages.finish_mailing(), reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return


@dp.callback_query_handler(lambda call: call.data == 'add_joke')
async def add_joke_handler(call: types.CallbackQuery):
    await bot.send_message(chat_id=call.message.chat.id,
                           text=bot_messages.new_joke(),
                           reply_markup=kb.cancel_keyboard())
    await dp.current_state().set_state("joke")


@dp.message_handler(user_id=admin_id, state="joke")
async def save_joke(message: types.Message, state: FSMContext):
    joke_text = message.text
    if joke_text == _("↩️Cancel"):
        await bot.send_message(chat_id=message.chat.id,
                               text=bot_messages.canceled(),
                               reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return
    else:
        await db.add_joke(joke_text)

        await message.reply(bot_messages.joke_added(),
                            reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        user_id = message.from_user.id
        logging.info(
            f"User action: Add joke (User ID: {user_id}), (Joke text: {message.text})"
        )


@dp.callback_query_handler(lambda call: call.data == 'daily_joke')
async def send_daily_joke(call: types.CallbackQuery):
    users = await db.get_private_users()
    await bot.send_message(chat_id=admin_id, text=bot_messages.start_mailing())
    for user in users:
        chat_id = user[0]
        try:

            language = await db.get_language(chat_id)

            table_name = f"jokes_{language}"

            result = await db.get_joke(chat_id, table_name)

            if not result:
                continue

            joke = result[0]
            joke_text = joke[1]

            await bot.send_message(
                chat_id=user[0],
                text=bot_messages.daily_joke(joke_text),
                parse_mode="Markdown",
                reply_markup=kb.return_rate_keyboard(joke[0]))

            await db.seen_joke(joke[0], chat_id)

            logging.info(f"Sent daily joke to user {chat_id}")
        except Exception as e:
            logging.error(f"Error sending message to user {chat_id}: {str(e)}")
            continue

    await bot.send_message(chat_id=admin_id, text=bot_messages.finish_mailing())


@dp.callback_query_handler(lambda call: call.data == 'control_user')
async def control_user_callback(call: types.CallbackQuery):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await call.message.answer(text=_('Search user by:'), reply_markup=kb.return_search_keyboard())


@dp.callback_query_handler(lambda call: call.data.startswith("search_"))
async def search_user_by(call: types.CallbackQuery):
    search = call.data.split('_')[1]
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await call.message.answer(text=_('Type user {search}:').format(search=search), reply_markup=kb.cancel_keyboard())

    await dp.current_state().set_state("control_user")
    await dp.current_state().update_data(search=search)


@dp.message_handler(state="control_user")
async def control_user(message: types.Message, state: FSMContext):
    answer = message.text
    answer = answer.replace("@", "")
    answer = answer.replace("https://t.me/", "")
    data = await state.get_data()
    search = data.get("search")

    if message.text == _("↩️Cancel"):
        await bot.send_message(message.chat.id,
                               'Action canceled!',
                               reply_markup=ReplyKeyboardRemove())
        await state.finish()

    else:
        await dp.bot.send_chat_action(message.chat.id, "typing")

        clock = await bot.send_message(message.chat.id, '⏳', reply_markup=ReplyKeyboardRemove())

        await asyncio.sleep(2)

        await bot.delete_message(message.chat.id, clock.message_id)

        user = None

        if search == "id":
            user = await db.get_user_info(answer)

        elif search == "username":
            user = await db.get_user_info_username(answer)

        if user is None:
            await bot.send_message(message.chat.id, _("User not found!"))

        result = user.fetchone()

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

            go_to_chat = InlineKeyboardButton(text=_("Enter in Conversation"), url=f"tg://user?id={user_id}")
            ban_button = InlineKeyboardButton(text=_("❌Ban"), callback_data=f"ban_{user_id}")
            unban_button = InlineKeyboardButton(text=_("✅Unban"), callback_data=f"unban_{user_id}")
            control_keyboard = InlineKeyboardMarkup()
            control_keyboard.row(go_to_chat)

            if user_username == "":
                user_username = "None"
            else:
                user_username = f"@{user_username}"

            user_photo = await bot.get_user_profile_photos(user_id, limit=1)

            if status == 'user':
                control_keyboard.row(ban_button)

            elif status == 'ban':
                control_keyboard.row(unban_button)

            if user_photo.total_count > 0:
                await message.reply_photo(user_photo.photos[0][-1].file_id,
                                          caption=bm.return_user_info(user_name, user_id, user_username, status),
                                          reply_markup=control_keyboard, parse_mode="Markdown")
            else:
                await bot.send_message(message.chat.id, bm.return_user_info(user_name, user_id, user_username, status),
                                       reply_markup=control_keyboard, parse_mode="Markdown")

        await state.finish()


@dp.callback_query_handler(lambda call: call.data.startswith("ban_"))
async def message_handler(call: types.CallbackQuery):
    banned_user_id = call.data.split("_")[1]
    user_status = await db.status(banned_user_id)

    if user_status == "admin":
        await call.message.edit_text(_("You cannot block yourself or another admin!"))
        pass

    else:
        await db.ban_user(banned_user_id)

        await call.message.delete()

        await call.message.answer(_("User {banned_user_id} successfully banned!").format(banned_user_id=banned_user_id))


@dp.callback_query_handler(lambda call: call.data.startswith("unban_"))
async def message_handler(call: types.CallbackQuery):
    unbanned_user_id = call.data.split("_")[1]
    user_status = await db.status(unbanned_user_id)

    if user_status == "admin":
        await call.message.edit_caption(_("You cannot unban yourself!"))
        pass

    else:
        await db.unban_user(unbanned_user_id)

        await call.message.delete()
        await call.message.answer(
            _("User {unbanned_user_id} successfully unbanned!").format(unbanned_user_id=unbanned_user_id))


@dp.message_handler(user_id=admin_id, commands=['info'])
async def info(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id
    language = await db.get_language(user_id)

    table_name = f"jokes_{language}"

    logging.info(f"User action: /info (User ID: {user_id})")

    joke_sent = await db.joke_sent(user_id)
    joke_count = await db.joke_count(table_name)
    sent_count = await db.sent_count()

    username = message.from_user.first_name

    await message.reply(
        bot_messages.admin_info(username, joke_sent, joke_count, sent_count), parse_mode='Markdown')


@dp.message_handler(user_id=admin_id, commands=['get_users'])
async def export_users_data(message: types.Message):
    # Виконуємо запит для отримання всіх даних з таблиці users

    users_data = await db.get_all_users_info()

    # Створюємо DataFrame з даними користувачів
    df = pd.DataFrame(users_data, columns=['user_id', 'chat_type', 'user_name', 'user_username', 'language', 'status'])

    # Створюємо Excel-файл з даними
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)

    # Збереження файлу на комп'ютері
    file_path = 'users_data.xlsx'
    with open(file_path, 'wb') as file:
        file.write(excel_file.getvalue())

    # Відправляємо Excel-файл у вашому Telegram-боті
    with open(file_path, 'rb') as file:
        await bot.send_document(chat_id=message.chat.id, document=file)

    # Видаляємо файл з комп'ютера
    os.remove(file_path)