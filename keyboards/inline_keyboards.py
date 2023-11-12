from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from main import _


def admin_keyboard():
    admin_keyboard = InlineKeyboardMarkup()
    add_joke_button = InlineKeyboardButton(text=_('📝Add a joke'), callback_data='add_joke')
    send_to_all_button = InlineKeyboardButton(text=_('💬Mailing'), callback_data='send_to_all')
    daily_joke_button = InlineKeyboardButton(text=_("🎭Joke of the day"), callback_data='daily_joke')
    download_log_button = InlineKeyboardButton(text=_("📄View log"), callback_data='download_log')
    delete_log_button = InlineKeyboardButton(text=_("❌📄Delete log"), callback_data='delete_log')
    control_user_button = InlineKeyboardButton(text=_("👤Control User"), callback_data='control_user')
    admin_keyboard.row(add_joke_button)
    admin_keyboard.row(send_to_all_button, daily_joke_button)
    admin_keyboard.row(download_log_button, delete_log_button)
    admin_keyboard.row(control_user_button)
    return admin_keyboard


def random_keyboard():
    random_button = InlineKeyboardButton(_('🔀Random joke'), callback_data="random_joke")
    category_button = InlineKeyboardButton(_('🔖Select category'), callback_data="select_category")
    random_keyboard = InlineKeyboardMarkup(row_width=2)
    random_keyboard.add(random_button)
    random_keyboard.add(category_button)
    return random_keyboard


def category_keyboard():
    гроші_button = InlineKeyboardButton(_('💵Money'), callback_data="joke:про_гроші")
    родина_button = InlineKeyboardButton(_('👨‍👩‍👦‍👦Family'), callback_data="joke:про_родину")
    білявки_button = InlineKeyboardButton(_('👱‍♀️Blondes'), callback_data="joke:про_білявок")
    теща_button = InlineKeyboardButton(_('👵Mother-in-law'), callback_data="joke:про_тещу")
    школа_button = InlineKeyboardButton(_('🏫School'), callback_data="joke:про_школу")
    вовочка_button = InlineKeyboardButton(_('👦Vovochka'), callback_data="joke:про_вовочку")
    медицина_button = InlineKeyboardButton(_('🏥Medicine'), callback_data="joke:про_медицину")
    студенти_button = InlineKeyboardButton(_('🎓Students'), callback_data="joke:про_студентів")
    робота_button = InlineKeyboardButton(_('🏢Work'), callback_data="joke:про_роботу")
    back_button = InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_random")
    category_keyboard = InlineKeyboardMarkup(row_width=2)
    category_keyboard.add(гроші_button, родина_button, білявки_button)
    category_keyboard.add(теща_button, школа_button, вовочка_button)
    category_keyboard.add(медицина_button, студенти_button, робота_button)
    category_keyboard.add(back_button)
    return category_keyboard


def cancel_keyboard():
    cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    cancel = KeyboardButton(_("↩️Cancel"))
    cancel_keyboard.add(cancel)
    return cancel_keyboard


lang_keyboard = InlineKeyboardMarkup()
lang_keyboard.add(InlineKeyboardButton(text="Українська🇺🇦", callback_data="lang_uk"),
                  InlineKeyboardButton(text="English🇬🇧", callback_data="lang_en"))


# Клавіатура для лайку і дизлайку
def return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id):
    like_button = InlineKeyboardButton(
        text=f'👍 {likes_count}', callback_data=f'like_{joke_id}')
    dislike_button = InlineKeyboardButton(
        text=f'👎 {dislikes_count}', callback_data=f'dislike_{joke_id}')
    rating_button = InlineKeyboardButton(
        text=_('📊Joke rate'), callback_data=f'rating_{joke_id}')
    rating_and_votes_keyboard = InlineKeyboardMarkup(row_width=2)
    rating_and_votes_keyboard.add(rating_button)
    rating_and_votes_keyboard.add(like_button, dislike_button)
    return rating_and_votes_keyboard


# Клавіатура для груп з додатковою кнопкою "Переглянути"
def return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id):
    like_button = InlineKeyboardButton(
        text=f'👍 {likes_count}', callback_data=f'like_{joke_id}')
    dislike_button = InlineKeyboardButton(
        text=f'👎 {dislikes_count}', callback_data=f'dislike_{joke_id}')
    rating_button = InlineKeyboardButton(
        text=_('📊Joke rate'), callback_data=f'rating_{joke_id}')
    seen_button = InlineKeyboardButton(
        text=_('👀Viewed'), callback_data=f'seen_{joke_id}')
    rating_and_seen_keyboard = InlineKeyboardMarkup(row_width=2)
    rating_and_seen_keyboard.add(rating_button)
    rating_and_seen_keyboard.add(like_button, dislike_button)
    rating_and_seen_keyboard.add(seen_button)
    return rating_and_seen_keyboard


def return_back_keyboard():
    keyboard = InlineKeyboardMarkup()
    back_button = InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_list")
    keyboard.row(back_button)
    return keyboard


def return_search_keyboard():
    search_keyboard = InlineKeyboardMarkup()
    id_button = InlineKeyboardButton(text="ID", callback_data="search_id")
    username_button = InlineKeyboardButton(text="Username", callback_data="search_username")
    back_button = InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")
    search_keyboard.row(username_button, id_button)
    search_keyboard.row(back_button)
    return search_keyboard


def return_back_to_admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    back_button = InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")
    keyboard.row(back_button)
    return keyboard


def return_feedback_button():
    keyboard = InlineKeyboardMarkup(row_width=2)
    feedback_button = InlineKeyboardButton(text=_("Feedback💬"), callback_data='feedback')
    keyboard.row(feedback_button)
    return keyboard


def feedback_answer(feedback_message_id, feedback_message_chat_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    answer_button = InlineKeyboardButton(text=_("Answer💬"),
                                         callback_data=f'answer_{feedback_message_id}_{feedback_message_chat_id}')
    keyboard.row(answer_button)
    return keyboard
