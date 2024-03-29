import asyncio
import logging
import re

from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from ping3 import ping

from config import *
from keyboards import inline_keyboards as kb
from main import dp, bot, _
from messages import bot_messages as bm
from middlewares.throttling_middleware import rate_limit
from services import DataBase

storage = MemoryStorage()

db = DataBase()


async def update_info(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_username = message.from_user.username
    referrer_id = None
    result = await db.user_exist(user_id)
    if result:
        await db.user_update_name(user_id, user_name, user_username)
    else:
        await db.add_users(user_id, user_name, user_username, "private", "uk", 'user', referrer_id)


@dp.message_handler(content_types=['new_chat_members'])
async def send_welcome(message: types.Message):
    for user in message.new_chat_members:
        if user.is_bot and user.id == bot.id:
            chat_info = await bot.get_chat(message.chat.id)
            chat_type = "public"
            user_id = message.chat.id
            user_name = chat_info.title
            user_username = None
            language = 'uk'
            status = 'user'
            referrer_id = None

            await db.add_users(user_id, user_name, user_username, chat_type, language, status, referrer_id)

            chat_title = chat_info.title
            await bot.send_message(
                chat_id=message.chat.id,
                text=bm.join_group(chat_title),
                parse_mode="Markdown")


@rate_limit(1)
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_username = message.from_user.username
    user_exist = await db.user_exist(user_id)

    await dp.bot.send_chat_action(message.chat.id, "typing")
    logging.info(f"User action: /start (User ID: {user_id})")

    await message.reply(bm.welcome_message(user_name))
    await message.answer(bm.pres_button(),
                         reply_markup=kb.random_keyboard())

    if 'bug' in message.get_args().lower():
        await message.answer(
            _('If you want to offer an anecdote or if you find a bug, please click the button below and describe it.'),
            reply_markup=kb.return_feedback_button())

    if 'ref' in message.get_args().lower():
        referrer_id = message.get_args().split('ref')[1]
        if referrer_id != '':
            if not user_exist:
                await db.add_users(user_id, user_name, user_username, "private", "uk", 'user', referrer_id)
                refs_count = await db.refs_count(referrer_id)
                try:
                    await bot.send_message(chat_id=referrer_id, text=_(
                        "Referral *{user_id}* has registered at your invitation!\nTotal number of invitees: *{refs_count}*").format(
                        user_id=user_id, refs_count=refs_count), parse_mode='Markdown')
                except Exception as e:
                    print(str(e))

    await update_info(message)


@rate_limit(1)
@dp.message_handler(commands=['language'])
async def change_lang(message: types.Message):
    user_id = message.from_user.id

    await bot.send_chat_action(user_id, 'typing')
    await asyncio.sleep(0.5)

    await message.reply(bm.please_choose(),
                        reply_markup=kb.lang_keyboard, parse_mode="Markdown")


@dp.callback_query_handler(lambda call: call.data.startswith('lang_'))
async def language_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    language = call.data.split('_')[1]
    await bot.send_chat_action(user_id, 'typing')
    await asyncio.sleep(0.5)
    await call.message.edit_text(text=bm.choose_lan(language))

    await db.set_language(user_id, language)
    await update_info(call.message)


@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")
    user_id = message.from_user.id

    table_name = f"jokes_uk"

    logging.info(f"User action: /info (User ID: {user_id})")

    joke_sent = await db.joke_sent(user_id)
    joke_count = await db.joke_count(table_name)
    sent_count = await db.sent_count()
    refs_count = await db.refs_count(user_id)
    ref_url = f't.me/{(await bot.get_me()).username}?start=ref{user_id}'

    username = message.from_user.first_name

    await message.reply(bm.user_info(username, joke_sent, joke_count, sent_count, refs_count, ref_url),
                        reply_markup=kb.return_feedback_button())
    await update_info(message)


@rate_limit(1)
@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /help (User ID: {user_id})")

    await message.reply(bm.help_message())
    await update_info(message)


@dp.message_handler(commands=['joke'])
@rate_limit(1)
async def handle_joke(message: types.Message):
    await dp.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /joke (User ID: {user_id})")

    await message.reply(bm.pres_button(),
                        reply_markup=kb.random_keyboard())
    await update_info(message)


@dp.message_handler(commands=['ping'])
async def cmd_ping(message: types.Message):
    try:
        response_time = ping("api.telegram.org", unit='ms')
        if response_time is not None:
            await message.answer(f"Ping: {response_time} ms")
        else:
            print("Сервер недоступний")
    except Exception as e:
        return str(e)


@dp.callback_query_handler(lambda call: call.data == 'feedback')
@rate_limit(1)
async def feedback_handler(call: types.CallbackQuery):
    await update_info(call.message)
    await call.message.delete()
    await call.message.answer(_('Please enter your message:'), reply_markup=kb.cancel_keyboard())
    await dp.current_state().set_state("send_feedback")
    await update_info(call.message)


@dp.message_handler(state="send_feedback")
async def feedback(message: types.Message, state: FSMContext):
    feedback_message = message.text
    feedback_message_id = message.message_id
    feedback_message_chat_id = message.chat.id
    user_id = message.from_user.id
    user_username = message.from_user.username

    if feedback_message == _("↩️Cancel"):
        await bot.send_message(message.chat.id,
                               _('Action canceled!'),
                               reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        await info(message)
        return

    if user_username is not None:
        user = "@" + user_username
    else:
        user = user_id

    await state.finish()

    await db.add_idea(feedback_message)

    await bot.send_message(chat_id=admin_id, text=bm.feedback_message_send(user, feedback_message),
                           reply_markup=kb.feedback_answer(feedback_message_id, feedback_message_chat_id),
                           parse_mode="Markdown")

    await message.answer(
        _("Your message *{feedback_message_id}* sent!").format(feedback_message_id=feedback_message_id),
        reply_markup=types.ReplyKeyboardRemove())
    await update_info(message)


@dp.callback_query_handler(lambda call: call.data == "select_category")
async def select_category(call):
    await call.message.edit_text(text=_('Please select category:'),
                                 reply_markup=kb.category_keyboard())


@dp.callback_query_handler(lambda call: call.data == "back_to_random")
async def back_to_random(call):
    await call.message.edit_text(bm.pres_button(), reply_markup=kb.random_keyboard())


async def send_joke(call, result):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    await dp.bot.send_chat_action(call.message.chat.id, "typing")

    if not result:
        await bot.send_message(chat_id, bm.all_send())

    else:
        joke = result[0]
        joke_id = joke[0]
        joke_text = joke[1]
        tags = await db.get_tags(joke_id)
        likes_count = await db.count_votes(joke_id, "like")
        dislikes_count = await db.count_votes(joke_id, "dislike")
        user_vote = await db.get_user_vote(joke_id, user_id)

        if tags is not None:
            tagged_tags = f'#{tags}'
            tagget_text = tagged_tags.replace(', ', ' #')
            joke = f'{joke_text}\n\n{tagget_text}'
        else:
            joke = joke_text

        joke_formated = re.sub(r"([*_`~]+)", r"\\\1", joke)
        keyboard_type = kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id)

        if call.message.chat.type == 'private':
            keyboard_type = kb.return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote)

        await call.message.edit_text(joke_formated, reply_markup=keyboard_type)
        await db.seen_joke(joke_id, user_id)
        logging.info(f"User action: Sent joke (User ID: {user_id}, Joke ID: {joke_id})")

    await bot.send_message(chat_id, text=bm.pres_button(), reply_markup=kb.random_keyboard())
    await update_info(call.message)


@dp.callback_query_handler(lambda call: call.data.startswith('joke:'))
async def send_category_joke_pivate(call):
    tag = call.data.split(':')[1]
    user_id = call.from_user.id
    result = await db.get_tagged_joke(user_id, tag)
    await send_joke(call, result)


@dp.callback_query_handler(lambda call: call.data == 'random_joke')
async def send_joke_private(call):
    user_id = call.from_user.id
    result = await db.get_joke(user_id)
    await send_joke(call, result)


scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(CronTrigger(hour=12))
async def daily_joke():
    users = await db.get_private_users()
    await bot.send_message(chat_id=admin_id, text=bm.start_mailing())
    result = await db.get_daily_joke()
    joke = result[0]
    joke_id = joke[0]
    joke_text = joke[1]

    for user in users:
        chat_id = user[0]
        try:

            if not result:
                continue

            tags = await db.get_tags(joke_id)

            likes_count = await db.count_votes(joke_id, "like")
            dislikes_count = await db.count_votes(joke_id, "dislike")
            user_vote = await db.get_user_vote(joke_id, chat_id)

            if tags is not None:
                tagged_tags = f'#{tags}'
                tagget_text = tagged_tags.replace(', ', ' #')
                joke = f'{joke_text}\n\n{tagget_text}'
            else:
                joke = joke_text

            joke_formated = re.sub(r"([*_`~]+)", r"\\\1", joke)

            await bot.send_message(
                chat_id=user[0],
                text=bm.daily_joke(joke_formated),
                parse_mode="Markdown",
                reply_markup=kb.return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote))

            await db.seen_joke(joke_id, chat_id)

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
        await call.answer(bm.already_seen_joke(), show_alert=True)
    else:
        await db.seen_joke(joke_id, user_id)
        await call.answer(bm.seen_joke(), show_alert=True)

    likes_count = await db.count_votes(joke_id, "like")
    dislikes_count = await db.count_votes(joke_id, "dislike")

    logging.info(
        f"User action: Marked joke as seen (User ID: {user_id}, Joke ID: {joke_id})"
    )

    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id))
    await update_info(call.message)

    await update_buttons(call.message, joke_id, user_id)


@dp.callback_query_handler(lambda call: call.data.startswith('like_'))
async def like_joke(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    user_vote = await db.get_user_vote(joke_id, user_id)

    if user_vote == "like":
        await db.remove_vote(joke_id, user_id)
        await call.answer(bm.revoked_vote())
        logging.info(
            f"User action: Removed like from joke (User ID: {user_id}, Joke ID: {joke_id})"
        )
    elif user_vote == "dislike":
        await db.update_vote(joke_id, user_id, "like")
        await call.answer(bm.liked_joke())
        logging.info(
            f"User action: Liked joke (User ID: {user_id}, Joke ID: {joke_id})"
        )
    else:
        await db.add_vote(joke_id, user_id, "like")
        await call.answer(bm.liked_joke())
        logging.info(
            f"User action: Liked joke (User ID: {user_id}, Joke ID: {joke_id})"
        )

    await update_buttons(call.message, joke_id, user_id)


@dp.callback_query_handler(lambda call: call.data.startswith('dislike_'))
async def dislike_joke(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    user_vote = await db.get_user_vote(joke_id, user_id)

    if user_vote == "dislike":
        await db.remove_vote(joke_id, user_id)
        await call.answer(bm.revoked_vote())
        logging.info(
            f"User action: Removed dislike from joke (User ID: {user_id}, Joke ID: {joke_id})"
        )
    elif user_vote == "like":
        await db.update_vote(joke_id, user_id, "dislike")
        await call.answer(bm.disliked_joke())
        logging.info(
            f"User action: Disliked joke (User ID: {user_id}, Joke ID: {joke_id})"
        )
    else:
        await db.add_vote(joke_id, user_id, "dislike")
        await call.answer(bm.disliked_joke())
        logging.info(
            f"User action: Disliked joke (User ID: {user_id}, Joke ID: {joke_id})"
        )

    await update_buttons(call.message, joke_id, user_id)


async def update_buttons(message, joke_id, user_id):
    likes_count = await db.count_votes(joke_id, "like")
    dislikes_count = await db.count_votes(joke_id, "dislike")
    user_vote = await db.get_user_vote(joke_id, user_id)

    if message.chat.type == 'private':
        reply_markup = kb.return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote)
    else:  # Для групових чатів
        reply_markup = kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id)

    try:
        await message.edit_reply_markup(reply_markup)

    except Exception as e:
        print(f"Error updating buttons: {e}")
        pass


@dp.callback_query_handler(lambda call: call.data.startswith('rating_'))
async def joke_rating(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    await update_buttons(call.message, joke_id, user_id)

    await call.answer(bm.updated_rating())


@dp.message_handler()
async def handle_message(message: types.Message):
    text = message.text.lower()
    name = message.from_user.full_name

    if "допомога" in text or "хелп" in text or "help" in text:
        await message.reply(bm.help_message())

    elif message.chat.type == 'private':
        await message.reply(bm.dont_understood(name), reply_markup=kb.return_feedback_button(), parse_mode="Markdown")

    elif message.chat.type == 'group' or message.chat.type == 'supergroup':
        pass
    await update_info(message)
