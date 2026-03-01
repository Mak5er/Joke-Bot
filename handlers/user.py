import asyncio
import logging

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, User
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from cachetools import TTLCache
from ping3 import ping

from app import bot, get_bot_username, i18n, send_analytics
from bot_utils import format_joke_text, is_cancel_action, is_unavailable_chat_error
from config import (
    DEFAULT_LOCALE,
    DEFAULT_PRIVATE_CHAT_TYPE,
    DEFAULT_PUBLIC_CHAT_TYPE,
    DEFAULT_USER_STATUS,
    JOKES_TABLE,
    admin_id,
)
from filters import ChatTypeF
from keyboards import inline_keyboards as kb
from messages import bot_messages as bm
from services import database as db

logger = logging.getLogger(__name__)
user_router = Router()
synced_users_cache: TTLCache[int, str] = TTLCache(maxsize=20_000, ttl=300)


class FindJoke(StatesGroup):
    find_joke = State()
    jokes_list = State()


class GiveFeedback(StatesGroup):
    feedback = State()


def normalize_user_chat_type(chat_type: str) -> str:
    if chat_type == DEFAULT_PRIVATE_CHAT_TYPE:
        return DEFAULT_PRIVATE_CHAT_TYPE
    return DEFAULT_PUBLIC_CHAT_TYPE


def resolve_user_locale(user: User) -> str:
    language_code = (user.language_code or DEFAULT_LOCALE).split("-", maxsplit=1)[0].lower()
    if language_code in {"uk", "en"}:
        return language_code
    return DEFAULT_LOCALE


async def get_user_locale(user: User) -> str:
    return await db.get_language(user.id) or resolve_user_locale(user)


async def sync_user(user: User, chat_type: str, referrer_id: int | None = None) -> None:
    normalized_chat_type = normalize_user_chat_type(chat_type)
    cached_chat_type = synced_users_cache.get(user.id)

    if referrer_id is None:
        if cached_chat_type == DEFAULT_PRIVATE_CHAT_TYPE:
            return
        if cached_chat_type == normalized_chat_type:
            return

    await db.sync_user(
        user.id,
        user.full_name,
        user.username,
        normalized_chat_type,
        resolve_user_locale(user),
        DEFAULT_USER_STATUS,
        referrer_id,
    )
    synced_users_cache[user.id] = normalized_chat_type


async def build_joke_payload(joke_id: int, user_id: int, chat_type: str, joke_text: str, user_locale: str):
    tags, likes_count, dislikes_count, user_vote = await db.get_joke_meta(joke_id, user_id)

    formatted_text = format_joke_text(joke_text, tags)
    if chat_type == DEFAULT_PRIVATE_CHAT_TYPE:
        keyboard = kb.return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote, user_locale)
    else:
        keyboard = kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id, user_locale)

    return formatted_text, keyboard


def extract_joke_id_from_message(message: types.Message) -> int | None:
    if message.reply_markup is None:
        return None

    for row in message.reply_markup.inline_keyboard:
        for button in row:
            callback_data = button.callback_data or ""
            for prefix in ("like_", "dislike_", "rating_", "seen_"):
                if callback_data.startswith(prefix):
                    joke_id = callback_data.split("_", maxsplit=1)[1]
                    if joke_id.isdigit():
                        return int(joke_id)

    return None


def has_expanded_joke_controls(message: types.Message) -> bool:
    if message.reply_markup is None:
        return False

    for row in message.reply_markup.inline_keyboard:
        for button in row:
            callback_data = button.callback_data or ""
            if callback_data in {"random_joke", "select_category"} or callback_data.startswith("seen_"):
                return True

    return False


def build_compact_rating_keyboard(
    likes_count: int,
    dislikes_count: int,
    joke_id: int,
    user_vote: str | None,
    chat_type: str,
    user_locale: str,
) -> InlineKeyboardMarkup:
    if chat_type == DEFAULT_PRIVATE_CHAT_TYPE:
        full_keyboard = kb.return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote, user_locale)
    else:
        full_keyboard = kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id, user_locale)

    return InlineKeyboardMarkup(inline_keyboard=full_keyboard.inline_keyboard[:2])


async def collapse_previous_joke_controls(message: types.Message, user_id: int, user_locale: str) -> None:
    if not has_expanded_joke_controls(message):
        return

    joke_id = extract_joke_id_from_message(message)
    if joke_id is None:
        return

    _, likes_count, dislikes_count, user_vote = await db.get_joke_meta(joke_id, user_id)
    reply_markup = build_compact_rating_keyboard(
        likes_count,
        dislikes_count,
        joke_id,
        user_vote,
        message.chat.type,
        user_locale,
    )

    try:
        await bot.edit_message_reply_markup(
            message_id=message.message_id,
            chat_id=message.chat.id,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest:
        logger.debug("Reply markup for archived joke %s did not change", joke_id)


async def send_joke(message: types.Message, user_id: int, result, user_locale: str):
    await bot.send_chat_action(message.chat.id, "typing")

    if not result:
        if message.chat.type == DEFAULT_PRIVATE_CHAT_TYPE:
            await bot.send_message(message.chat.id, bm.all_send(), reply_markup=kb.random_keyboard(user_locale))
        else:
            try:
                await message.edit_text(bm.all_send(), reply_markup=kb.random_keyboard(user_locale))
            except TelegramBadRequest:
                await bot.send_message(message.chat.id, bm.all_send(), reply_markup=kb.random_keyboard(user_locale))
        return

    joke = result[0]
    joke_id = joke[0]
    joke_text = joke[1]
    formatted_text, keyboard = await build_joke_payload(joke_id, user_id, message.chat.type, joke_text, user_locale)
    await collapse_previous_joke_controls(message, user_id, user_locale)
    await message.answer(formatted_text, reply_markup=keyboard)


    await db.seen_joke(joke_id, user_id)
    logger.info("Sent joke %s to user %s", joke_id, user_id)


@user_router.message(ChatTypeF(["group", "supergroup"]), F.new_chat_member)
async def send_group_welcome(message: types.Message):
    for member in message.new_chat_members:
        if not member.is_bot or member.id != bot.id:
            continue

        chat_info = await bot.get_chat(message.chat.id)
        await db.add_users(
            message.chat.id,
            chat_info.title,
            None,
            DEFAULT_PUBLIC_CHAT_TYPE,
            DEFAULT_LOCALE,
            DEFAULT_USER_STATUS,
            None,
        )
        await bot.send_message(message.chat.id, bm.join_group(chat_info.title))


@user_router.message(CommandStart())
async def send_welcome(message: types.Message, command: CommandObject):
    user = message.from_user
    user_locale = await get_user_locale(user)
    await bot.send_chat_action(message.chat.id, "typing")

    await message.answer(
        f"{bm.welcome_message(user.full_name)}\n\n{bm.pres_button()}",
        reply_markup=kb.random_keyboard(user_locale),
    )

    referrer_id = None
    args = command.args or ""
    if args.startswith("ref"):
        raw_referrer_id = args.removeprefix("ref").strip()
        if raw_referrer_id.isdigit():
            referrer_id = int(raw_referrer_id)

    user_exists = await db.user_exist(user.id)
    if referrer_id and not user_exists and referrer_id != user.id:
        await sync_user(user, message.chat.type, referrer_id=referrer_id)
        refs_count = await db.refs_count(referrer_id)
        try:
            await bot.send_message(referrer_id, bm.refferal_joined(user.id, refs_count))
        except Exception:
            logger.warning("Failed to notify referrer %s", referrer_id, exc_info=True)
    else:
        await sync_user(user, message.chat.type)

    await send_analytics(user_id=user.id, user_lang_code=user.language_code, action_name="start")
    logger.info("User action: /start (user_id=%s)", user.id)


@user_router.message(Command("language"))
async def change_lang(message: types.Message):
    await sync_user(message.from_user, message.chat.type)
    await bot.send_chat_action(message.chat.id, "typing")
    await message.reply(bm.please_choose(), reply_markup=kb.lang_keyboard())
    await send_analytics(
        user_id=message.from_user.id,
        user_lang_code=message.from_user.language_code,
        action_name="change_language",
    )


@user_router.callback_query(F.data.startswith("lang_"))
async def language_callback(call: types.CallbackQuery):
    language = call.data.split("_", maxsplit=1)[1]
    await db.set_language(call.from_user.id, language)
    synced_users_cache[call.from_user.id] = normalize_user_chat_type(call.message.chat.type)
    await sync_user(call.from_user, call.message.chat.type)
    await call.message.edit_text(text=bm.choose_lan(language), reply_markup=kb.random_keyboard(language))
    await call.answer()


@user_router.message(Command("info"))
async def info(message: types.Message):
    await sync_user(message.from_user, message.chat.type)
    await bot.send_chat_action(message.chat.id, "typing")
    user_locale = await get_user_locale(message.from_user)

    user_id = message.from_user.id
    joke_sent, joke_count, sent_count, refs_count = await asyncio.gather(
        db.joke_sent(user_id),
        db.joke_count(JOKES_TABLE),
        db.sent_count(),
        db.refs_count(user_id),
    )
    ref_url = f"t.me/{await get_bot_username()}?start=ref{user_id}"

    await message.reply(
        bm.user_info(message.from_user.first_name, joke_sent, joke_count, sent_count, refs_count, ref_url),
        reply_markup=kb.return_feedback_button(user_locale),
    )
    await send_analytics(user_id=user_id, user_lang_code=message.from_user.language_code, action_name="info")


@user_router.message(Command("help"))
async def send_help(message: types.Message):
    await sync_user(message.from_user, message.chat.type)
    await bot.send_chat_action(message.chat.id, "typing")
    await message.reply(bm.help_message())
    await send_analytics(user_id=message.from_user.id, user_lang_code=message.from_user.language_code, action_name="help")


@user_router.message(Command("joke"))
async def handle_joke(message: types.Message):
    await sync_user(message.from_user, message.chat.type)
    await bot.send_chat_action(message.chat.id, "typing")
    await message.reply(bm.pres_button(), reply_markup=kb.random_keyboard(await get_user_locale(message.from_user)))
    await send_analytics(
        user_id=message.from_user.id,
        user_lang_code=message.from_user.language_code,
        action_name="joke_command",
    )


@user_router.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await sync_user(message.from_user, message.chat.type)
    response_time = await asyncio.to_thread(ping, "api.telegram.org", unit="ms")
    if response_time is None:
        await message.answer("Ping is unavailable right now.")
    else:
        await message.answer(f"Ping: {response_time:.2f} ms")

    await send_analytics(
        user_id=message.from_user.id,
        user_lang_code=message.from_user.language_code,
        action_name="check_ping",
    )


@user_router.callback_query(F.data == "feedback")
async def feedback_handler(call: types.CallbackQuery, state: FSMContext):
    await sync_user(call.from_user, call.message.chat.type)
    await bot.send_chat_action(call.message.chat.id, "typing")
    await call.message.answer(bm.please_enter_message(), reply_markup=kb.cancel_keyboard())
    await state.set_state(GiveFeedback.feedback)
    await call.answer()
    await send_analytics(user_id=call.from_user.id, user_lang_code=call.from_user.language_code, action_name="feedback")


@user_router.message(GiveFeedback.feedback)
async def feedback(message: types.Message, state: FSMContext):
    if is_cancel_action(message.text):
        await bot.send_message(message.chat.id, bm.action_canceled(), reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        await bot.send_message(
            message.chat.id,
            bm.pres_button(),
            reply_markup=kb.random_keyboard(await get_user_locale(message.from_user)),
        )
        return

    await sync_user(message.from_user, message.chat.type)
    await state.clear()
    await db.add_idea(message.text)

    user_label = f"@{message.from_user.username}" if message.from_user.username else message.from_user.id
    await bot.send_message(
        admin_id,
        bm.feedback_message_send(user_label, message.text),
        reply_markup=kb.feedback_answer(message.message_id, message.chat.id),
    )
    await message.answer(
        bm.your_message_sent_with_id(message.message_id),
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await bot.send_message(
        message.chat.id,
        bm.pres_button(),
        reply_markup=kb.random_keyboard(await get_user_locale(message.from_user)),
    )


@user_router.callback_query(F.data == "select_category")
async def select_category(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    user_locale = await get_user_locale(call.from_user)
    if call.message.chat.type == DEFAULT_PRIVATE_CHAT_TYPE:
        await collapse_previous_joke_controls(call.message, call.from_user.id, user_locale)
        await call.message.answer(text=bm.select_category(), reply_markup=kb.category_keyboard(user_locale))
    else:
        await call.message.edit_text(text=bm.select_category(), reply_markup=kb.category_keyboard(user_locale))
    await call.answer()


@user_router.callback_query(F.data == "back_to_random")
async def back_to_random(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    await call.message.edit_text(bm.pres_button(), reply_markup=kb.random_keyboard(await get_user_locale(call.from_user)))
    await call.answer()


@user_router.callback_query(F.data.startswith("joke:"))
async def send_category_joke_private(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    tag = call.data.split(":", maxsplit=1)[1]
    result = await db.get_tagged_joke(call.from_user.id, tag)
    await send_joke(call.message, call.from_user.id, result, await get_user_locale(call.from_user))
    await call.answer()
    await send_analytics(
        user_id=call.from_user.id,
        user_lang_code=call.from_user.language_code,
        action_name=f"get_joke_by_category_{tag}",
    )


@user_router.callback_query(F.data == "random_joke")
async def send_joke_private(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    result = await db.get_joke(call.from_user.id)
    await send_joke(call.message, call.from_user.id, result, await get_user_locale(call.from_user))
    await call.answer()
    await send_analytics(
        user_id=call.from_user.id,
        user_lang_code=call.from_user.language_code,
        action_name="get_joke",
    )


@user_router.message(Command("find"))
async def return_find_menu(message: types.Message, state: FSMContext):
    await sync_user(message.from_user, message.chat.type)
    await bot.send_chat_action(message.chat.id, "typing")
    await message.reply(bm.type_joke_text_or_id(), reply_markup=kb.cancel_keyboard())
    await state.set_state(FindJoke.find_joke)


@user_router.message(FindJoke.find_joke)
async def find_jokes(message: types.Message, state: FSMContext):
    answer = (message.text or "").strip()
    if is_cancel_action(answer):
        await bot.send_message(message.chat.id, bm.action_canceled(), reply_markup=types.ReplyKeyboardRemove())
        await bot.send_message(
            message.chat.id,
            bm.pres_button(),
            reply_markup=kb.random_keyboard(await get_user_locale(message.from_user)),
        )
        await state.clear()
        return

    await sync_user(message.from_user, message.chat.type)
    if answer.isdigit():
        result = await db.get_joke_by_id(int(answer))
    else:
        result = await db.get_joke_by_text(answer)

    if not result:
        await bot.send_message(message.chat.id, bm.nothing_found(), reply_markup=ReplyKeyboardRemove())
        await bot.send_message(
            message.chat.id,
            bm.pres_button(),
            reply_markup=kb.random_keyboard(await get_user_locale(message.from_user)),
        )
        await state.clear()
        return

    await state.set_state(FindJoke.jokes_list)
    await state.update_data(jokes=result)
    await show_joke_page(message, 0, state)
    await send_analytics(user_id=message.from_user.id, user_lang_code=message.from_user.language_code, action_name="find_joke")


@user_router.callback_query(F.data.startswith("joke_"))
async def show_joke(call: types.CallbackQuery, state: FSMContext):
    await sync_user(call.from_user, call.message.chat.type)
    joke_id = int(call.data.split("_", maxsplit=1)[1])
    result = await db.get_joke_by_id(joke_id)
    if not result:
        await call.answer(bm.nothing_found(), show_alert=True)
        return

    formatted_text, keyboard = await build_joke_payload(
        joke_id,
        call.from_user.id,
        call.message.chat.type,
        result[0][1],
        await get_user_locale(call.from_user),
    )
    await call.message.answer(f"ID: {joke_id}\n\n{formatted_text}", reply_markup=keyboard)
    await db.seen_joke(joke_id, call.from_user.id)
    await state.clear()
    await call.answer()
    logger.info("Sent joke %s to user %s from search", joke_id, call.from_user.id)


@user_router.callback_query(F.data.startswith("page_"))
async def jokes_pagination(call: types.CallbackQuery, state: FSMContext):
    await sync_user(call.from_user, call.message.chat.type)
    page_number = int(call.data.split("_", maxsplit=1)[1])
    await show_joke_page(call.message, page_number, state)
    await call.answer()


@user_router.callback_query(F.data == "page_number")
async def noop_page_callback(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    await call.answer()


async def show_joke_page(message: types.Message, page_number: int, state: FSMContext):
    data = await state.get_data()
    jokes = data.get("jokes", [])
    if not jokes:
        await message.answer(bm.nothing_found(), reply_markup=ReplyKeyboardRemove())
        return

    page_size = 10
    total_pages = (len(jokes) - 1) // page_size + 1
    safe_page_number = max(0, min(page_number, total_pages - 1))
    current_page = jokes[safe_page_number * page_size : (safe_page_number + 1) * page_size]

    builder = InlineKeyboardBuilder()
    for joke in current_page:
        joke_text_short = joke[1][:30] + "..." if len(joke[1]) > 30 else joke[1]
        builder.row(InlineKeyboardButton(text=f"#{joke[0]} {joke_text_short}", callback_data=f"joke_{joke[0]}"))

    navigation_row = []
    if safe_page_number > 0:
        navigation_row.append(InlineKeyboardButton(text="<", callback_data=f"page_{safe_page_number - 1}"))

    navigation_row.append(
        InlineKeyboardButton(text=f"{_('Page ')}{safe_page_number + 1}/{total_pages}", callback_data="page_number")
    )

    if safe_page_number < total_pages - 1:
        navigation_row.append(InlineKeyboardButton(text=">", callback_data=f"page_{safe_page_number + 1}"))

    builder.row(*navigation_row)

    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=bm.pick_a_joke(),
            reply_markup=builder.as_markup(),
        )
    except TelegramBadRequest:
        await message.answer(text=bm.pick_a_joke(), reply_markup=builder.as_markup())


async def daily_joke():
    users = await db.get_private_users()
    admin_locale = await db.get_language(admin_id) or DEFAULT_LOCALE
    await bot.send_message(chat_id=admin_id, text=bm.start_mailing(i18n, admin_locale))

    result = await db.get_daily_joke()
    if not result:
        await bot.send_message(chat_id=admin_id, text=bm.all_send())
        return

    joke = result[0]
    joke_id = joke[0]
    joke_text = joke[1]
    tags, likes_count, dislikes_count, _ = await db.get_joke_meta(joke_id, admin_id)
    formatted_joke = format_joke_text(joke_text, tags)
    user_ids = [user[0] for user in users]
    user_locales = await db.get_languages_for_users(user_ids)
    user_votes = await db.get_votes_for_users(joke_id, user_ids)

    for user in users:
        chat_id = user[0]
        try:
            user_locale = user_locales.get(chat_id) or DEFAULT_LOCALE
            user_vote = user_votes.get(chat_id)
            await bot.send_message(
                chat_id=chat_id,
                text=bm.daily_joke(i18n, user_locale, formatted_joke),
                reply_markup=kb.return_rating_and_votes_keyboard_mailing(
                    i18n,
                    user_locale,
                    likes_count,
                    dislikes_count,
                    joke_id,
                    user_vote,
                ),
            )
            await db.seen_joke(joke_id, chat_id)
            logger.info("Sent daily joke to user %s", chat_id)
            await asyncio.sleep(0.05)
        except Exception as error:
            logger.error("Error sending daily joke to user %s: %s", chat_id, error)
            if is_unavailable_chat_error(error):
                await db.set_inactive(chat_id)

    await bot.send_message(chat_id=admin_id, text=bm.finish_mailing(i18n, admin_locale))


@user_router.callback_query(F.data.startswith("seen_"))
async def seen_handling(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    joke_id = int(call.data.split("_", maxsplit=1)[1])
    existing_row = await db.check_seen_joke(joke_id, call.from_user.id)

    if existing_row:
        await call.answer(bm.already_seen_joke(), show_alert=True)
    else:
        await db.seen_joke(joke_id, call.from_user.id)
        await call.answer(bm.seen_joke(), show_alert=True)

    await update_buttons(call.message, joke_id, call.from_user.id, await get_user_locale(call.from_user))
    logger.info("User %s marked joke %s as seen", call.from_user.id, joke_id)


@user_router.callback_query(F.data.startswith("like_"))
async def like_joke(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    joke_id = int(call.data.split("_", maxsplit=1)[1])
    user_vote = await db.get_user_vote(joke_id, call.from_user.id)

    if user_vote == "like":
        await db.remove_vote(joke_id, call.from_user.id)
        await call.answer(bm.revoked_vote())
        action_name = "removed_like"
    elif user_vote == "dislike":
        await db.update_vote(joke_id, call.from_user.id, "like")
        await call.answer(bm.liked_joke())
        action_name = "liked"
    else:
        await db.add_vote(joke_id, call.from_user.id, "like")
        await call.answer(bm.liked_joke())
        action_name = "liked"

    await update_buttons(call.message, joke_id, call.from_user.id, await get_user_locale(call.from_user))
    await send_analytics(user_id=call.from_user.id, user_lang_code=call.from_user.language_code, action_name=action_name)


@user_router.callback_query(F.data.startswith("dislike_"))
async def dislike_joke(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    joke_id = int(call.data.split("_", maxsplit=1)[1])
    user_vote = await db.get_user_vote(joke_id, call.from_user.id)

    if user_vote == "dislike":
        await db.remove_vote(joke_id, call.from_user.id)
        await call.answer(bm.revoked_vote())
        action_name = "removed_dislike"
    elif user_vote == "like":
        await db.update_vote(joke_id, call.from_user.id, "dislike")
        await call.answer(bm.disliked_joke())
        action_name = "disliked"
    else:
        await db.add_vote(joke_id, call.from_user.id, "dislike")
        await call.answer(bm.disliked_joke())
        action_name = "disliked"

    await update_buttons(call.message, joke_id, call.from_user.id, await get_user_locale(call.from_user))
    await send_analytics(user_id=call.from_user.id, user_lang_code=call.from_user.language_code, action_name=action_name)


async def update_buttons(message: types.Message, joke_id: int, user_id: int, user_locale: str):
    _, likes_count, dislikes_count, user_vote = await db.get_joke_meta(joke_id, user_id)

    if has_expanded_joke_controls(message):
        if message.chat.type == DEFAULT_PRIVATE_CHAT_TYPE:
            reply_markup = kb.return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote, user_locale)
        else:
            reply_markup = kb.return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id, user_locale)
    else:
        reply_markup = build_compact_rating_keyboard(
            likes_count,
            dislikes_count,
            joke_id,
            user_vote,
            message.chat.type,
            user_locale,
        )

    try:
        await bot.edit_message_reply_markup(message_id=message.message_id, chat_id=message.chat.id, reply_markup=reply_markup)
    except TelegramBadRequest:
        logger.debug("Reply markup for joke %s did not change", joke_id)


@user_router.callback_query(F.data.startswith("rating_"))
async def joke_rating(call: types.CallbackQuery):
    await sync_user(call.from_user, call.message.chat.type)
    joke_id = int(call.data.split("_", maxsplit=1)[1])
    await update_buttons(call.message, joke_id, call.from_user.id, await get_user_locale(call.from_user))
    await call.answer(bm.updated_rating())
    await send_analytics(user_id=call.from_user.id, user_lang_code=call.from_user.language_code, action_name="update_rating")


@user_router.message()
async def handle_message(message: types.Message):
    if not message.text:
        return

    text = message.text.casefold()
    if "допомога" in text or "хелп" in text or "help" in text:
        await sync_user(message.from_user, message.chat.type)
        await message.reply(bm.help_message())
        return

    if message.chat.type == DEFAULT_PRIVATE_CHAT_TYPE:
        await sync_user(message.from_user, message.chat.type)
        await message.reply(
            f"{bm.dont_understood(message.from_user.full_name)}",
            reply_markup=kb.return_feedback_button(await get_user_locale(message.from_user)),
        )
