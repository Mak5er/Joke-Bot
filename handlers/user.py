import asyncio
import datetime
import logging
import os
import time

import openai as openai
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
from main import dp, bot
from messages import bot_messages
from services import DataBase

OPENAI_TOKEN = Config.token_openai

storage = MemoryStorage()

db = DataBase('services/jokes.db')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/bot_log.log")
handler.setFormatter(custom_formatter)

logger.addHandler(handler)

last_joke_button = {}

last_joke_command = {}

last_info_command = {}

last_help_command = {}

last_admin_command = {}

openai.api_key = OPENAI_TOKEN


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
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_username = message.from_user.username

    await db.add_users(user_id, user_name, user_username, "private")

    logging.info(f"User action: /start (User ID: {user_id})")

    await message.reply(bot_messages.welcome_message(user_name))


@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    if message.chat.type == 'private':
        user_id = message.from_user.id
        current_time = time.time()

        if user_id in last_admin_command:
            last_command_time = last_admin_command[user_id]
            elapsed_time = current_time - last_command_time

            if elapsed_time < 3:
                await message.answer(
                    "Ви використали команду /admin занадто часто. Будь ласка, зачекайте."
                )
                return

        last_admin_command[user_id] = current_time

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
async def info(message: types.Message):
    user_id = message.from_user.id

    current_time = time.time()

    if user_id in last_info_command:
        last_command_time = last_info_command[user_id]
        elapsed_time = current_time - last_command_time

        if elapsed_time < 3:
            await message.reply(
                "Ви використали команду /info занадто часто. Будь ласка, зачекайте."
            )
            return

    last_info_command[user_id] = current_time

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
async def send_help(message: types.Message):
    user_id = message.from_user.id

    current_time = time.time()

    if user_id in last_help_command:
        last_command_time = last_help_command[user_id]
        elapsed_time = current_time - last_command_time

        if elapsed_time < 3:
            await message.reply(
                "Ви використали команду /help занадто часто. Будь ласка, зачекайте."
            )
            return

    last_joke_command[user_id] = current_time

    logging.info(f"User action: /help (User ID: {user_id})")

    await message.reply(bot_messages.help_message())


@dp.message_handler(commands=['joke'])
async def handle_joke(message: types.Message):
    user_id = message.from_user.id
    current_time = time.time()

    if user_id in last_joke_command:
        last_command_time = last_joke_command[user_id]
        elapsed_time = current_time - last_command_time

        if elapsed_time < 3:
            await message.reply(
                "Ви використовуєте команду /joke занадто часто. Будь ласка, зачекайте."
            )
            return

    last_joke_command[user_id] = current_time

    logging.info(f"User action: /joke (User ID: {user_id})")

    await message.reply("Натисни на кнопку, щоб отримати анекдот.",
                        reply_markup=inline_keyboards.random_keyboard)


@dp.message_handler(commands=['ai_joke'])
async def handle_joke(message: types.Message):
    user_id = message.from_user.id
    current_time = time.time()

    if user_id in last_joke_command:
        last_command_time = last_joke_command[user_id]
        elapsed_time = current_time - last_command_time

        if elapsed_time < 3:
            await message.reply(
                "Ви використовуєте команду /ai_joke занадто часто. Будь ласка, зачекайте."
            )
            return

    last_joke_command[user_id] = current_time

    logging.info(f"User action: /ai_joke (User ID: {user_id})")

    await message.reply("Натисни на кнопку, щоб згенерувати анекдот.",
                        reply_markup=inline_keyboards.ai_keyboard)


@dp.message_handler(commands=['dellog'])
async def del_log(message: types.Message):
    user_id = message.from_user.id
    if user_id == Config.admin_id:
        logging.shutdown()
        open('log/bot_log.log', 'w').close()
        await message.reply("Лог видалено, починаю записувати новий.")


@dp.message_handler(commands=['downloaddb'])
async def download_db(message: types.Message):
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
                               text="Розсилку завершено!", reply_markup=types.ReplyKeyboardRemove())
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


@dp.callback_query_handler(lambda call: call.data == 'ai_joke')
async def ai_joke_handler(call: types.CallbackQuery):
    await bot.send_message(chat_id=call.message.chat.id, text="На яку тему або про що має бути анекдот?")
    await dp.current_state().set_state("ai_joke")


@dp.message_handler(state="ai_joke")
async def ai_joke(message: types.Message, state: FSMContext):
    clock = await bot.send_message(chat_id=message.chat.id, text="⏳")

    theme = message.text
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"привіт, згенеруй для мене анекдот на тему {theme}, відповідь лише українською мовою, відповідь має бути такою Анекдот для вас: і згенерований анекдот",
        max_tokens=512,
        temperature=0.7,
        n=1,
        stop=None,
    )
    generated_joke = response.choices[0].text.strip()

    await bot.edit_message_text(text=f"{generated_joke}", chat_id=message.chat.id, message_id=clock.message_id)

    await state.finish()
    user_id = message.from_user.id
    logging.info(f"User action: Ai joke (User ID: {user_id})")

    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.send_message(chat_id=message.chat.id,
                           text="Натисни на кнопку, щоб згенерувати анекдот.",
                           reply_markup=inline_keyboards.ai_keyboard)


@dp.callback_query_handler(ChatTypeFilter(types.ChatType.PRIVATE),
                           lambda call: call.data == 'random_joke')
async def send_joke_private(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    current_time = time.time()

    if user_id in last_joke_button:
        last_button_time = last_joke_button[user_id]
        elapsed_time = current_time - last_button_time

        if elapsed_time < 3:
            await bot.answer_callback_query(
                call.id, "Ви натискаєте занадто часто. Зачекайте.")
            return

    last_joke_button[user_id] = current_time

    result = await db.get_joke(user_id)

    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    if not result:
        await bot.send_message(
            chat_id, 'На жаль, всі анекдоти вже були надіслані вам.')
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
                           text="Натисни на кнопку, щоб отримати анекдот.",
                           reply_markup=inline_keyboards.random_keyboard)


@dp.callback_query_handler(
    ChatTypeFilter(types.ChatType.GROUP)
    | ChatTypeFilter(types.ChatType.SUPERGROUP),
    lambda call: call.data == 'random_joke')
async def send_joke_group(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    current_time = time.time()

    if user_id in last_joke_button:
        last_button_time = last_joke_button[user_id]
        elapsed_time = current_time - last_button_time

        if elapsed_time < 3:
            await bot.answer_callback_query(
                call.id, "Ви натискаєте занадто часто. Зачекайте.")
            return

    last_joke_button[user_id] = current_time

    result = await db.get_joke(user_id)

    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    if not result:
        await bot.send_message(
            chat_id, 'На жаль, всі анекдоти вже були надіслані вам.')
    else:
        joke = result[0]
        joke_id = joke[0]

        await call.answer("Ви проголосували за анекдот!")

        await bot.send_message(
            chat_id,
            joke[1],
            reply_markup=inline_keyboards.return_seen_rate_keyboard(joke_id))

        logging.info(
            f"User action: Sent joke (User ID: {user_id}, Joke ID: {joke[0]})")

    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    await bot.send_message(chat_id,
                           text="Натисни на кнопку, щоб отримати анекдот.",
                           reply_markup=inline_keyboards.random_keyboard)


@dp.callback_query_handler(lambda call: call.data == 'daily_joke')
async def send_daily_joke(call: types.CallbackQuery):
    users = await db.get_private_users()
    await bot.send_message(chat_id=Config.admin_id, text="Починаю розсилку...")
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
                           text="Розсилку завершено!")


scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(CronTrigger(hour=9))
async def job():
    print(">>>>", datetime.datetime.now())
    users = await db.get_private_users()
    await bot.send_message(chat_id=Config.admin_id, text="Починаю розсилку...")
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

    await bot.send_message(chat_id=Config.admin_id, text="Розсилку завершено!")


@dp.callback_query_handler(lambda call: call.data.startswith('seen_'))
async def seen_handling(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    existing_row = await db.check_seen_joke(joke_id, user_id)

    if existing_row:
        await call.answer("Ви вже відмічали цей анекдот як прочитаний!")
    else:
        await db.seen_joke(joke_id, user_id)
        await call.answer("Ви відмітили цей анекдот як прочитаний!")

    joke_seens = await db.joke_seens(joke_id)

    await call.answer("Ви прочитали анекдот!")

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
    await call.answer("Ви прочитали анекдот!")


@dp.callback_query_handler(lambda call: call.data.startswith('like_'))
async def like_joke(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    await db.like_joke(joke_id)

    joke_rate = await db.joke_rate(joke_id)

    await call.answer("Ви проголосували за анекдот!")

    await call.message.edit_reply_markup(
        reply_markup=inline_keyboards.return_rating_keyboard(joke_rate))
    await asyncio.sleep(5)
    await call.message.edit_reply_markup(
        reply_markup=inline_keyboards.return_hidden_rating_keyboard(joke_id))

    logging.info(
        f"User action: Liked joke (User ID: {user_id}, Joke ID: {joke_id})")


@dp.callback_query_handler(lambda call: call.data.startswith('dislike_'))
async def dislike_joke(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    await db.dislike_joke(joke_id)

    joke_rate = await db.joke_rate(joke_id)

    await call.answer("Ви проголосували проти анекдота!")
    await call.message.edit_reply_markup(
        reply_markup=inline_keyboards.return_rating_keyboard(joke_rate))
    await asyncio.sleep(5)
    await call.message.edit_reply_markup(
        reply_markup=inline_keyboards.return_hidden_rating_keyboard(joke_id))

    logging.info(
        f"User action: Disliked joke (User ID: {user_id}, Joke ID: {joke_id})")


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

    await bot.answer_callback_query(call.id, f"📊Рейтинг анекдота: {joke_rate}")

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

    await bot.answer_callback_query(call.id, f"📊Рейтинг анекдота: {joke_rate}")


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
