import asyncio
import datetime
import logging
import os

from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import ChatMemberUpdated
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config
from keyboards import inline_keyboards
from log.logger import custom_formatter
from main import dp, bot, rate_limit
from messages import bot_messages
from services import DataBase

storage = MemoryStorage()

db = DataBase('services/jokes.db')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/bot_log.log")
handler.setFormatter(custom_formatter)

logger.addHandler(handler)


@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def bot_added_to_chat(event: ChatMemberUpdated):
    if event.from_user.id == event.chat.id:
        chat_info = await bot.get_chat(event.chat.id)
        chat_type = "public"
        user_id = event.chat.id
        user_name = None
        user_username = None

        await db.add_users(user_id, user_name, user_username, chat_type)

        if chat_info.permissions.can_send_messages:
            await bot.send_message(
                chat_id=event.chat.id,
                text=f"""Привіт! Дякую, що додали мене в *'{event.chat.title}'* 
    Для коректної роботи прошу надати мені права адміністратора!""",
                parse_mode="Markdown")

        logging.info(
            f"User action: Bot added to group(Group name: {event.chat.title})")


@dp.message_handler(commands=['start'])
@rate_limit(3)
async def send_welcome(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_username = message.from_user.username

    await db.add_users(user_id, user_name, user_username, "private")

    logging.info(f"User action: /start (User ID: {user_id})")

    await message.reply(bot_messages.welcome_message(user_name))


@dp.message_handler(commands=['admin'])
@rate_limit(5)
async def admin(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    if message.chat.type == 'private':
        user_id = message.from_user.id

        logging.info(f"User action: /admin (User ID: {user_id})")

        if user_id == Config.admin_id:

            user_count = await db.user_count()
            joke_count = await db.joke_count()
            sent_count = await db.sent_count()

            await message.answer(bot_messages.admin_panel(
                user_count, joke_count, sent_count),
                reply_markup=inline_keyboards.admin_keyboard)
        else:
            await message.answer("У вас немає прав адміністратора!")
    else:
        await message.answer("Цю команду не можна використовувати в групі!")


@dp.message_handler(commands=['info'])
@rate_limit(3)
async def info(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /info (User ID: {user_id})")

    joke_sent = await db.joke_sent(user_id)
    joke_count = await db.joke_count()
    sent_count = await db.sent_count()

    username = message.from_user.first_name

    if message.chat.type == 'private' and user_id == Config.admin_id:
        await message.reply(
            bot_messages.admin_info(username, joke_sent, joke_count,
                                    sent_count))

    else:
        await message.reply(
            bot_messages.user_info(username, joke_sent, joke_count,
                                   sent_count))


@dp.message_handler(commands=['help'])
@rate_limit(3)
async def send_help(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /help (User ID: {user_id})")

    await message.reply(bot_messages.help_message())


@dp.message_handler(commands=['joke'])
@rate_limit(3)
async def handle_joke(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /joke (User ID: {user_id})")

    await message.reply("Натисни на кнопку, щоб отримати анекдот.",
                        reply_markup=inline_keyboards.random_keyboard)


@dp.message_handler(commands=['del_log'])
@rate_limit(10)
async def del_log(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id
    if user_id == Config.admin_id:
        logging.shutdown()
        open('log/bot_log.log', 'w').close()
        await message.reply("Лог видалено, починаю записувати новий.")


@dp.message_handler(commands=['download_db'])
@rate_limit(10)
async def download_db(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id
    if user_id == Config.admin_id:
        db_file = 'services/jokes.db'
        if os.path.exists(db_file):
            with open(db_file, 'rb') as file:
                await bot.send_document(message.chat.id, file)
                logging.info(
                    f"User action: Downloaded db (User ID: {user_id})")
        else:
            await bot.send_message(message.chat.id, 'Db file not found.')


@dp.callback_query_handler(lambda call: call.data == 'download_log')
async def download_log_handler(call: types.CallbackQuery):
    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    log_file = 'log/bot_log.log'
    user_id = call.from_user.id

    if os.path.exists(log_file):
        with open(log_file, 'rb') as file:
            await bot.send_document(call.message.chat.id, file)
            logging.info(f"User action: Downloaded log (User ID: {user_id})")
    else:
        await bot.send_message(call.message.chat.id, 'Log file not found.')


@dp.callback_query_handler(lambda call: call.data == 'send_to_all')
async def send_to_all_callback(call: types.CallbackQuery):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    cancel = types.KeyboardButton("↩️Скасувати")
    keyboard.add(cancel)

    await bot.send_message(chat_id=call.message.chat.id,
                           text='Введіть повідомлення для відправлення:',
                           reply_markup=keyboard)
    await dp.current_state().set_state("send_to_all_message")


@dp.message_handler(state="send_to_all_message")
async def send_to_all_message(message: types.Message, state: FSMContext):
    sender_id = message.from_user.id
    if message.text == "↩️Скасувати":
        await bot.send_message(message.chat.id,
                               'Відправлення скасовано!',
                               reply_markup=types.ReplyKeyboardRemove())
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
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    cancel = types.KeyboardButton("↩️Скасувати")
    keyboard.add(cancel)

    await bot.send_message(chat_id=call.message.chat.id,
                           text="Введи новий анекдот:",
                           reply_markup=keyboard)
    await dp.current_state().set_state("joke")


@dp.message_handler(state="joke")
async def save_joke(message: types.Message, state: FSMContext):
    joke_text = message.text
    if joke_text == "↩️Скасувати":
        await bot.send_message(chat_id=message.chat.id,
                               text='Додавання скасовано!',
                               reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return
    else:
        await db.add_joke(joke_text)

        await message.reply(f"Анекдот додано до бази даних.",
                            reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        user_id = message.from_user.id
        logging.info(
            f"User action: Add joke (User ID: {user_id}), (Joke text: {message.text})"
        )


@dp.callback_query_handler(ChatTypeFilter(types.ChatType.PRIVATE),
                           lambda call: call.data == 'random_joke')
async def send_joke_private(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    result = await db.get_joke(user_id)

    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    if not result:
        await bot.send_message(
            chat_id, bot_messages.all_send())
    else:
        joke = result[0]

        joke_id = joke[0]

        joke_text = joke[1]

        await bot.send_message(
            chat_id,
            joke_text,
            reply_markup=inline_keyboards.return_rate_keyboard(joke_id))

        await db.seen_joke(joke_id, user_id)

        logging.info(
            f"User action: Sent joke (User ID: {user_id}, Joke ID: {joke[0]})")

    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    await bot.send_message(chat_id,
                           text=bot_messages.prees_button(),
                           reply_markup=inline_keyboards.random_keyboard)


@dp.callback_query_handler(
    ChatTypeFilter(types.ChatType.GROUP)
    | ChatTypeFilter(types.ChatType.SUPERGROUP),
    lambda call: call.data == 'random_joke')
async def send_joke_group(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    result = await db.get_joke(user_id)

    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    if not result:
        await bot.send_message(
            chat_id, bot_messages.all_send())
    else:
        joke = result[0]
        joke_id = joke[0]

        await bot.send_message(
            chat_id,
            joke[1],
            reply_markup=inline_keyboards.return_seen_rate_keyboard(joke_id))

        logging.info(
            f"User action: Sent joke (User ID: {user_id}, Joke ID: {joke[0]})")

    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    await bot.send_message(chat_id,
                           text=bot_messages.prees_button(),
                           reply_markup=inline_keyboards.random_keyboard)


@dp.callback_query_handler(lambda call: call.data == 'daily_joke')
async def send_daily_joke(call: types.CallbackQuery):
    users = await db.get_private_users()
    await bot.send_message(chat_id=Config.admin_id, text=bot_messages.start_mailing())
    for user in users:
        chat_id = user[0]
        try:

            result = await db.get_joke(chat_id)

            if not result:
                continue

            joke = result[0]

            await bot.send_message(
                chat_id=user[0],
                text=f"*Анекдот дня:*\n\n{joke[1]}",
                parse_mode="Markdown",
                reply_markup=inline_keyboards.return_rate_keyboard(joke[0]))

            await db.seen_joke(joke[0], chat_id)

            logging.info(f"Sent daily joke to user {chat_id}")
        except Exception as e:
            logging.error(f"Error sending message to user {chat_id}: {str(e)}")
            continue

    await bot.send_message(chat_id=call.message.chat.id,
                           text=bot_messages.finish_mailing())


scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(CronTrigger(hour=9))
async def job():
    print(">>>>", datetime.datetime.now())
    users = await db.get_private_users()
    await bot.send_message(chat_id=Config.admin_id, text=bot_messages.start_mailing())
    for user in users:
        chat_id = user[0]
        try:

            result = await db.get_joke(chat_id)

            if not result:
                continue

            joke = result[0]

            await bot.send_message(
                chat_id=user[0],
                text=f"*Анекдот дня:*\n\n{joke[1]}",
                parse_mode="Markdown",
                reply_markup=inline_keyboards.return_rate_keyboard(joke[0]))

            await db.seen_joke(joke[0], chat_id)

            logging.info(f"Sent daily joke to user {chat_id}")
        except Exception as e:
            logging.error(f"Error sending message to user {chat_id}: {str(e)}")
            continue

    await bot.send_message(chat_id=Config.admin_id, text=bot_messages.finish_mailing())


# noinspection PyArgumentList
@dp.callback_query_handler(lambda call: call.data.startswith('seen_'))
async def seen_handling(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    existing_row = await db.check_seen_joke(joke_id, user_id)

    if existing_row:
        await call.answer(bot_messages.already_seen_joke())
    else:
        await db.seen_joke(joke_id, user_id)
        await call.answer(bot_messages.seen_joke())

    joke_seens = await db.joke_seens(joke_id)

    logging.info(
        f"User action: Marked joke as seen (User ID: {user_id}, Joke ID: {joke_id})"
    )

    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=inline_keyboards.return_seen_count_rate_keyboard(
            joke_seens, joke_id))
    await asyncio.sleep(3)
    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=inline_keyboards.return_seen_rate_keyboard(joke_id))


@dp.callback_query_handler(lambda call: call.data.startswith('seeen_'))
async def seen_button_handling(call: types.CallbackQuery):
    await call.answer(bot_messages.already_seen_joke())


@dp.callback_query_handler(lambda call: call.data.startswith('like_'))
async def like_joke(call: types.CallbackQuery):
    # noinspection PyArgumentList
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    await db.like_joke(joke_id)

    joke_rate = await db.joke_rate(joke_id)

    await call.answer(bot_messages.liked_joke())

    await call.message.edit_reply_markup(
        reply_markup=inline_keyboards.return_rating_keyboard(joke_rate))
    await asyncio.sleep(5)
    await call.message.edit_reply_markup(
        reply_markup=inline_keyboards.return_hidden_rating_keyboard(joke_id))

    logging.info(
        f"User action: Liked joke (User ID: {user_id}, Joke ID: {joke_id})")


# noinspection PyArgumentList
@dp.callback_query_handler(lambda call: call.data.startswith('dislike_'))
async def dislike_joke(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    await db.dislike_joke(joke_id)

    joke_rate = await db.joke_rate(joke_id)

    await call.answer(bot_messages.disliked_joke())
    await call.message.edit_reply_markup(
        reply_markup=inline_keyboards.return_rating_keyboard(joke_rate))
    await asyncio.sleep(5)
    await call.message.edit_reply_markup(
        reply_markup=inline_keyboards.return_hidden_rating_keyboard(joke_id))

    logging.info(
        f"User action: Disliked joke (User ID: {user_id}, Joke ID: {joke_id})")


# noinspection PyArgumentList
@dp.callback_query_handler(ChatTypeFilter(types.ChatType.PRIVATE),
                           lambda call: call.data.startswith('rate_'))
async def rate_joke_private(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])

    joke_rate = await db.joke_rate(joke_id)

    await bot.answer_callback_query(call.id, f"📊Рейтинг анекдота: {joke_rate}")

    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=inline_keyboards.return_rating_keyboard(joke_rate))
    await asyncio.sleep(5)
    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=inline_keyboards.return_hidden_rating_keyboard(joke_id))


@dp.callback_query_handler(
    ChatTypeFilter(types.ChatType.GROUP)
    | ChatTypeFilter(types.ChatType.SUPERGROUP),
    lambda call: call.data.startswith('rate_'))
async def rate_joke_group(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])

    joke_rate = await db.joke_rate(joke_id)

    await bot.answer_callback_query(call.id, bot_messages.joke_rating(joke_rate))

    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=inline_keyboards.return_rating_and_seen_keyboard(
            joke_rate, joke_id))
    await asyncio.sleep(5)
    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=inline_keyboards.return_seen_rate_keyboard(joke_id))


@dp.callback_query_handler(lambda call: call.data.startswith('rating_'))
async def joke_rating(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])

    joke_rate = await db.joke_rate(joke_id)

    await bot.answer_callback_query(call.id, bot_messages.joke_rating(joke_rate))


@dp.message_handler()
async def handle_message(message: types.Message):
    text = message.text.lower()
    name = message.from_user.full_name

    if "допомога" in text or "хелп" in text or "help" in text:
        await message.reply(bot_messages.help_message())

    elif message.chat.type == 'private':
        await message.reply(
            f'*{name}*, вас не розумію! Введіть команду /help щоб отримати список команд!',
            parse_mode="Markdown")
