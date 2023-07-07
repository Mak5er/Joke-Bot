import logging

from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from config import *
from keyboards import inline_keyboards
from log.logger import custom_formatter
from main import dp, bot, rate_limit, _
from messages import bot_messages
from services import DataBase

storage = MemoryStorage()

db = DataBase('services/jokes.db')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/bot_log.log")
handler.setFormatter(custom_formatter)

logger.addHandler(handler)


@dp.message_handler(user_id=admin_id, commands=['admin'])
@rate_limit(5)
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
            reply_markup=inline_keyboards.admin_keyboard())
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
                           reply_markup=inline_keyboards.cancel_keyboard())
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
                           reply_markup=inline_keyboards.cancel_keyboard())
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
                reply_markup=inline_keyboards.return_rate_keyboard(joke[0]))

            await db.seen_joke(joke[0], chat_id)

            logging.info(f"Sent daily joke to user {chat_id}")
        except Exception as e:
            logging.error(f"Error sending message to user {chat_id}: {str(e)}")
            continue

    await bot.send_message(chat_id=admin_id, text=bot_messages.finish_mailing())


@dp.message_handler(user_id=admin_id, commands=['info'])
@rate_limit(3)
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
        bot_messages.admin_info(username, joke_sent, joke_count, sent_count))
