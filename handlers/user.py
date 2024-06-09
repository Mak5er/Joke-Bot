import asyncio
import logging
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from filters import ChatTypeF
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, ReplyKeyboardRemove

from ping3 import ping

from config import *
from keyboards import inline_keyboards as kb
from main import send_analytics, bot, i18n
from messages import bot_messages as bm
from services import DataBase

db = DataBase()

user_router = Router()


class FindJoke(StatesGroup):
    find_joke = State()
    jokes_list = State()


class GiveFeedback(StatesGroup):
    feedback = State()


async def update_info(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_username = message.from_user.username
    referrer_id = None
    result = await db.user_exist(user_id)
    if result:
        await db.user_update_name(user_id, user_name, user_username)
    else:
        await db.add_users(user_id, user_name, user_username, "private", "uk", 'active', referrer_id)


@user_router.message(ChatTypeF('group'), F.new_chat_member)
async def send_welcome(message: types.Message):
    for user in message.new_chat_members:
        if user.is_bot and user.id == bot.id:
            chat_info = await bot.get_chat(message.chat.id)
            chat_type = "public"
            user_id = message.chat.id
            user_name = chat_info.title
            user_username = None
            language = 'uk'
            status = 'active'
            referrer_id = None

            await db.add_users(user_id, user_name, user_username, chat_type, language, status, referrer_id)

            chat_title = chat_info.title
            await bot.send_message(
                chat_id=message.chat.id,
                text=bm.join_group(chat_title),
                parse_mode="HTML")


@user_router.message(CommandStart())
async def send_welcome(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_username = message.from_user.username
    user_exist = await db.user_exist(user_id)

    await bot.send_chat_action(message.chat.id, "typing")

    await message.reply(bm.welcome_message(user_name))

    await message.answer(bm.pres_button(),
                         reply_markup=kb.random_keyboard())

    args = command.args
    if args is not None:

        if 'ref' in args:
            referrer_id = args.split('ref')[1]
            if referrer_id != '':
                if not user_exist:
                    await db.add_users(user_id, user_name, user_username, "private", "uk", 'user', referrer_id)
                    refs_count = await db.refs_count(referrer_id)
                    try:
                        await bot.send_message(chat_id=referrer_id, text=bm.refferal_joined(user_id, refs_count),
                                               parse_mode='HTML')
                    except Exception as e:
                        print(str(e))

    await update_info(message)

    await send_analytics(user_id=message.from_user.id,
                         user_lang_code=message.from_user.language_code,
                         action_name='start')

    logging.info(f"User action: /start (User ID: {user_id})")


@user_router.message(Command('language'))
async def change_lang(message: types.Message):
    user_id = message.from_user.id
    await bot.send_chat_action(user_id, 'typing')

    await message.reply(bm.please_choose(),
                        reply_markup=kb.lang_keyboard(), parse_mode="HTML")

    await send_analytics(user_id=user_id, user_lang_code=message.from_user.language_code, action_name='change_language')


@user_router.callback_query(F.data.startswith('lang_'))
async def language_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    language = call.data.split('_')[1]
    await call.message.edit_text(text=bm.choose_lan(language))

    await db.set_language(user_id, language)
    await call.answer()

    await update_info(call.message)


@user_router.message(Command('info'))
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

    await message.reply(bm.user_info(username, joke_sent, joke_count, sent_count, refs_count, ref_url),
                        reply_markup=kb.return_feedback_button())
    await update_info(message)

    await send_analytics(user_id=user_id, user_lang_code=message.from_user.language_code, action_name='info')


@user_router.message(Command('help'))
async def send_help(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /help (User ID: {user_id})")

    await message.reply(bm.help_message())
    await update_info(message)

    await send_analytics(user_id=user_id, user_lang_code=message.from_user.language_code, action_name='help')


@user_router.message(Command('joke'))
async def handle_joke(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id

    logging.info(f"User action: /joke (User ID: {user_id})")

    await message.reply(bm.pres_button(),
                        reply_markup=kb.random_keyboard())
    await update_info(message)

    await send_analytics(user_id=user_id, user_lang_code=message.from_user.language_code, action_name='joke_command')


@user_router.message(Command('ping'))
async def cmd_ping(message: types.Message):
    try:
        response_time = ping("api.telegram.org", unit='ms')
        if response_time is not None:
            await message.answer(f"Ping: {response_time} ms")
        else:
            print("Сервер недоступний")
    except Exception as e:
        return str(e)

    await send_analytics(user_id=message.from_user.id, user_lang_code=message.from_user.language_code,
                         action_name='check_ping')


@user_router.callback_query(F.data == "feedback")
async def feedback_handler(call: types.CallbackQuery, state: FSMContext):
    await bot.send_chat_action(call.message.chat.id, "typing")
    await call.message.answer(bm.please_enter_message(), reply_markup=kb.cancel_keyboard())
    await state.set_state(GiveFeedback.feedback)
    await call.answer()
    await update_info(call.message)
    await send_analytics(user_id=call.from_user.id, user_lang_code=call.from_user.language_code, action_name='info')


@user_router.message(GiveFeedback.feedback)
async def feedback(message: types.Message, state: FSMContext):
    feedback_message = message.text
    feedback_message_id = message.message_id
    feedback_message_chat_id = message.chat.id
    user_id = message.from_user.id
    user_username = message.from_user.username

    if feedback_message == _("↩️Cancel"):
        await bot.send_message(message.chat.id,
                               bm.action_canceled(),
                               reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        await info(message)
        return

    if user_username is not None:
        user = "@" + user_username
    else:
        user = user_id

    await state.clear()

    await db.add_idea(feedback_message)

    await bot.send_message(chat_id=admin_id, text=bm.feedback_message_send(user, feedback_message),
                           reply_markup=kb.feedback_answer(feedback_message_id, feedback_message_chat_id),
                           parse_mode="HTML")

    await message.answer(
        bm.your_message_sent_with_id(feedback_message_id),
        reply_markup=types.ReplyKeyboardRemove())
    await update_info(message)


@user_router.callback_query(F.data == "select_category")
async def select_category(call):
    await call.message.edit_text(text=bm.select_category(),
                                 reply_markup=kb.category_keyboard())


@user_router.callback_query(F.data == "back_to_random")
async def back_to_random(call):
    await call.message.edit_text(bm.pres_button(), reply_markup=kb.random_keyboard())


async def send_joke(user_id, message, result):
    await bot.send_chat_action(message.chat.id, "typing")

    if not result:
        await bot.send_message(user_id, bm.all_send())

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

        keyboard_type = kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id)

        if message.chat.type == 'private':
            keyboard_type = kb.return_rating_and_votes_keyboard(likes_count,
                                                                dislikes_count, joke_id, user_vote)

        await message.edit_text(joke, reply_markup=keyboard_type)
        await db.seen_joke(joke_id, user_id)
        logging.info(f"User action: Sent joke (User ID: {user_id}, Joke ID: {joke_id})")

    await bot.send_message(user_id, text=bm.pres_button(), reply_markup=kb.random_keyboard())
    await update_info(message)


@user_router.callback_query(F.data.startswith('joke:'))
async def send_category_joke_pivate(call):
    tag = call.data.split(':')[1]
    user_id = call.from_user.id
    result = await db.get_tagged_joke(user_id, tag)
    await send_joke(user_id, call.message, result)
    await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code,
                         action_name=f'get_joke_by_category_{tag}')


@user_router.callback_query(F.data == 'random_joke')
async def send_joke_private(call):
    user_id = call.from_user.id
    result = await db.get_joke(user_id)
    await send_joke(user_id, call.message, result)
    await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code, action_name='get_joke')


@user_router.message(Command('find'))
async def return_find_menu(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.reply(bm.type_joke_text_or_id(), reply_markup=kb.cancel_keyboard())
    await state.set_state(FindJoke.find_joke)


@user_router.message(FindJoke.find_joke)
async def find_jokes(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    answer = message.text

    if answer == _("↩️Cancel"):
        await bot.send_message(message.chat.id,
                               bm.action_canceled(),
                               reply_markup=types.ReplyKeyboardRemove())
        return

    result = None

    if answer.isdigit():
        result = await db.get_joke_by_id(int(answer))
    elif answer:
        result = await db.get_joke_by_text(answer)

    if not result:
        await bot.send_message(user_id, bm.nothing_found())
        return

    await state.update_data(jokes=result)

    clock = await bot.send_message(message.chat.id, '⏳', reply_markup=ReplyKeyboardRemove())

    await bot.delete_message(message.chat.id, clock.message_id)

    # Start the dialog for pagination
    await show_joke_page(message, 0, state)

    await send_analytics(user_id=user_id, user_lang_code=message.from_user.language_code, action_name='find_joke')


@user_router.callback_query(F.data.startswith('joke_'))
async def show_joke(call: types.CallbackQuery):
    user_id = call.from_user.id

    tag = call.data.split('_')[1]

    result = await db.get_joke_by_id(tag)

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

    keyboard_type = kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id)

    if call.message.chat.type == 'private':
        keyboard_type = kb.return_rating_and_votes_keyboard(likes_count,
                                                            dislikes_count, joke_id, user_vote)

    await call.message.answer(f"ID: {joke_id}")
    await call.message.answer(joke, reply_markup=keyboard_type)
    await db.seen_joke(joke_id, user_id)
    await call.answer()
    logging.info(f"User action: Sent joke (User ID: {user_id}, Joke ID: {joke_id})")


@user_router.callback_query(F.data.startswith('page_'))
async def jokes_pagination(call: types.CallbackQuery, state: FSMContext):
    page_number = int(call.data.split('_')[1])

    await show_joke_page(call.message, page_number, state)
    await call.answer()

    await asyncio.sleep(600)
    await state.clear()


async def show_joke_page(message: types.Message, page_number: int, state: FSMContext):
    data = await state.get_data()

    jokes = data.get("jokes", [])  # Retrieve jokes data from state
    page_size = 10
    current_page = jokes[page_number * page_size:(page_number + 1) * page_size]

    # Create the inline keyboard markup
    builder = InlineKeyboardBuilder()

    previous_page_button = InlineKeyboardButton(text="⬅️", callback_data=f"page_{page_number - 1}")
    page_number_button = InlineKeyboardButton(text=_("Page ") + str(int(page_number + 1)),
                                              callback_data="page_number")
    next_page_button = InlineKeyboardButton(text="➡️", callback_data=f"page_{page_number + 1}")

    # Add joke buttons
    for joke in current_page:
        joke_text_short = joke[1][:30] + "..." if len(joke[1]) > 30 else joke[1]
        button = InlineKeyboardButton(text=joke_text_short, callback_data=f"joke_{joke[0]}")
        builder.row(button)

    if page_number > 0:
        builder.row(previous_page_button)

        # Add navigation buttons (if applicable)
    if len(jokes) > (page_number + 1) * page_size:
        page_number_button = InlineKeyboardButton(text=_("Page ") + str(int(page_number + 1)),
                                                  callback_data="page_number")
        if page_number == 0:
            builder.row(page_number_button)
        else:
            builder.add(page_number_button)

        builder.add(next_page_button)

    elif page_number > 0:
        builder.add(page_number_button)

    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=bm.pick_a_joke(),
            reply_markup=builder.as_markup(),
        )
    except:
        await message.answer(
            text=bm.pick_a_joke(),
            reply_markup=builder.as_markup(),
        )


async def daily_joke():
    users = await db.get_private_users()
    await bot.send_message(chat_id=admin_id, text=bm.start_mailing(i18n, await db.get_language(admin_id)))
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

            await bot.send_message(
                chat_id=user[0],
                text=bm.daily_joke(i18n, await db.get_language(user[0]), joke),
                parse_mode="HTML",
                reply_markup=kb.return_rating_and_votes_keyboard_mailing(i18n, await db.get_language(chat_id),
                                                                         likes_count,
                                                                         dislikes_count, joke_id, user_vote))

            await db.seen_joke(joke_id, chat_id)

            logging.info(f"Sent daily joke to user {chat_id}")

            user_status = await db.status(chat_id)

            if user_status == "inactive":
                await db.set_active(chat_id)

            await asyncio.sleep(
                0.05
            )

        except Exception as e:
            logging.error(f"Error sending message to user {chat_id}: {str(e)}")

            if str(e) == "Forbidden: bots can't send messages to bots":
                await db.delete_user(chat_id)

            if "blocked" or "Chat not found" in str(e):
                await db.set_inactive(chat_id)

            continue

    await bot.send_message(chat_id=admin_id, text=bm.finish_mailing(i18n, await db.get_language(admin_id)))


@user_router.callback_query(F.data.startswith('seen_'))
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


@user_router.callback_query(F.data.startswith('like_'))
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
        await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code, action_name='removed_like')

    elif user_vote == "dislike":
        await db.update_vote(joke_id, user_id, "like")
        await call.answer(bm.liked_joke())
        logging.info(
            f"User action: Liked joke (User ID: {user_id}, Joke ID: {joke_id})"
        )
        await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code, action_name='liked')

    else:
        await db.add_vote(joke_id, user_id, "like")
        await call.answer(bm.liked_joke())
        logging.info(
            f"User action: Liked joke (User ID: {user_id}, Joke ID: {joke_id})"
        )
        await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code, action_name='liked')

    await update_buttons(call.message, joke_id, user_id)


@user_router.callback_query(F.data.startswith('dislike_'))
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
        await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code,
                             action_name='removed_dislike')

    elif user_vote == "like":
        await db.update_vote(joke_id, user_id, "dislike")
        await call.answer(bm.disliked_joke())
        logging.info(
            f"User action: Disliked joke (User ID: {user_id}, Joke ID: {joke_id})"
        )
        await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code, action_name='disliked')

    else:
        await db.add_vote(joke_id, user_id, "dislike")
        await call.answer(bm.disliked_joke())
        logging.info(
            f"User action: Disliked joke (User ID: {user_id}, Joke ID: {joke_id})"
        )
        await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code, action_name='disliked')

    await update_buttons(call.message, joke_id, user_id)


async def update_buttons(message, joke_id, user_id):
    likes_count = await db.count_votes(joke_id, "like")
    dislikes_count = await db.count_votes(joke_id, "dislike")
    user_vote = await db.get_user_vote(joke_id, user_id)

    if message.chat.type == 'private':
        reply_markup = kb.return_rating_and_votes_keyboard(likes_count,
                                                           dislikes_count, joke_id, user_vote)
    else:  # Для групових чатів
        reply_markup = kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id)

    try:
        await bot.edit_message_reply_markup(message_id=message.message_id, chat_id=message.chat.id,
                                            reply_markup=reply_markup)

    except Exception as e:
        print(f"Error updating buttons: {e}")
        pass


@user_router.callback_query(F.data.startswith('rating_'))
async def joke_rating(call: types.CallbackQuery):
    joke_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    await update_buttons(call.message, joke_id, user_id)

    await call.answer(bm.updated_rating())

    await send_analytics(user_id=user_id, user_lang_code=call.from_user.language_code, action_name='update_rating')


@user_router.message()
async def handle_message(message: types.Message):
    text = message.text.lower()
    name = message.from_user.full_name

    if "допомога" in text or "хелп" in text or "help" in text:
        await message.reply(bm.help_message())

    elif message.chat.type == 'private':
        await message.reply(bm.dont_understood(name), reply_markup=kb.return_feedback_button(), parse_mode="HTML")

    elif message.chat.type == 'group' or message.chat.type == 'supergroup':
        pass
    await update_info(message)
