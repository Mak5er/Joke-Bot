import asyncio
import datetime
import logging

from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import ChatTypeFilter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import *
from keyboards import inline_keyboards
from log.logger import custom_formatter
from main import dp, bot
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


@dp.message_handler(content_types=['new_chat_members'])
async def send_welcome(message: types.Message):
    bot_obj = await bot.get_me()
    bot_id = bot_obj.id

    for chat_member in message.new_chat_members:
        chat_info = await bot.get_chat(message.chat.id)
        chat_type = "public"
        user_id = message.chat.id
        user_name = None
        user_username = None

        await db.add_users(user_id, user_name, user_username, chat_type)

        chat_title = chat_info.title
        if chat_member.id == bot_id:
            await bot.send_message(
                chat_id=message.chat.id,
                text=bm.join_group(chat_title),
                parse_mode="Markdown")


@rate_limit(1)
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_username = message.from_user.username

    await db.add_users(user_id, user_name, user_username, "private")

    logging.info(f"User action: /start (User ID: {user_id})")

    await message.reply(bm.welcome_message(user_name))


@rate_limit(1)
@dp.message_handler(commands=['language'])
async def change_lang(message: types.Message):
    user_id = message.from_user.id

    await bot.send_chat_action(user_id, 'typing')
    await asyncio.sleep(0.5)

    await message.reply(bm.please_choose(),
                        reply_markup=inline_keyboards.lang_keyboard, parse_mode="Markdown")


@dp.callback_query_handler(lambda call: call.data.startswith('lang_'))
async def language_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    language = call.data.split('_')[1]
    await bot.send_chat_action(user_id, 'typing')
    await asyncio.sleep(0.5)
    await call.message.edit_text(text=bm.choose_lan(language))

    await db.set_language(user_id, language)


@dp.message_handler(commands=['info'])
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

    await message.reply(bm.user_info(username, joke_sent, joke_count, sent_count))


@rate_limit(1)
@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /help (User ID: {user_id})")

    await message.reply(bm.help_message())


@dp.message_handler(commands=['joke'])
@rate_limit(1)
async def handle_joke(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /joke (User ID: {user_id})")

    await message.reply(bm.pres_button(),
                        reply_markup=inline_keyboards.random_keyboard())


@dp.callback_query_handler(ChatTypeFilter(types.ChatType.PRIVATE),
                           lambda call: call.data == 'random_joke')
async def send_joke_private(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = await db.get_language(user_id)

    table_name = f"jokes_{language}"

    result = await db.get_joke(user_id, table_name)

    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    if not result:
        await bot.send_message(
            chat_id, bm.all_send())
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
                           text=bm.pres_button(),
                           reply_markup=inline_keyboards.random_keyboard())


@dp.callback_query_handler(
    ChatTypeFilter(types.ChatType.GROUP)
    | ChatTypeFilter(types.ChatType.SUPERGROUP),
    lambda call: call.data == 'random_joke')
async def send_joke_group(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = await db.get_language(user_id)

    table_name = f"jokes_{language}"

    result = await db.get_joke(user_id, table_name)

    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    if not result:
        await bot.send_message(
            chat_id, bm.all_send())
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
                           text=bm.pres_button(),
                           reply_markup=inline_keyboards.random_keyboard())


scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(CronTrigger(hour=12))
async def job():
    print(">>>>", datetime.datetime.now())
    users = await db.get_private_users()
    await bot.send_message(chat_id=admin_id, text=bm.start_mailing())
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
                text=bm.daily_joke(joke_text),
                parse_mode="Markdown",
                reply_markup=inline_keyboards.return_rate_keyboard(joke[0]))

            await db.seen_joke(joke[0], chat_id)

            logging.info(f"Sent daily joke to user {chat_id}")
        except Exception as e:
            logging.error(f"Error sending message to user {chat_id}: {str(e)}")
            continue

    await bot.send_message(chat_id=admin_id, text=bm.finish_mailing())


@dp.callback_query_handler(lambda call: call.data.startswith('seen_'))
async def seen_handling(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    existing_row = await db.check_seen_joke(joke_id, user_id)

    if existing_row:
        await call.answer(bm.already_seen_joke())
    else:
        await db.seen_joke(joke_id, user_id)
        await call.answer(bm.seen_joke())

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
    await call.answer(bm.already_seen_joke())


@dp.callback_query_handler(lambda call: call.data.startswith('like_'))
async def like_joke(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id
    language = await db.get_language(user_id)

    table_name = f"jokes_{language}"

    await db.like_joke(joke_id, table_name)

    joke_rate = await db.joke_rate(joke_id, table_name)

    await call.answer(bm.liked_joke())

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
    language = await db.get_language(user_id)

    table_name = f"jokes_{language}"

    await db.dislike_joke(joke_id, table_name)

    joke_rate = await db.joke_rate(joke_id, table_name)

    await call.answer(bm.disliked_joke())
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
    user_id = call.from_user.id
    language = await db.get_language(user_id)

    table_name = f"jokes_{language}"

    joke_rate = await db.joke_rate(joke_id, table_name)

    await bot.answer_callback_query(call.id, bm.joke_rating(joke_rate))

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
    user_id = call.from_user.id
    language = await db.get_language(user_id)

    table_name = f"jokes_{language}"

    joke_rate = await db.joke_rate(joke_id, table_name)

    await bot.answer_callback_query(call.id, bm.joke_rating(joke_rate))

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
    user_id = call.from_user.id
    language = await db.get_language(user_id)

    table_name = f"jokes_{language}"

    joke_rate = await db.joke_rate(joke_id, table_name)

    await bot.answer_callback_query(call.id, bm.joke_rating(joke_rate))


@dp.message_handler()
async def handle_message(message: types.Message):
    text = message.text.lower()
    name = message.from_user.full_name

    if "допомога" in text or "хелп" in text or "help" in text:
        await message.reply(bm.help_message())

    elif message.chat.type == 'private':
        await message.reply(bm.dont_understood(name), parse_mode="Markdown")
