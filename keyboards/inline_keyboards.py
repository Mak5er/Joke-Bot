from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from main import _

admin_keyboard = InlineKeyboardMarkup()
add_joke_button = InlineKeyboardButton(text=_('📝Add a joke'),
                                       callback_data='add_joke')
send_to_all_button = InlineKeyboardButton(
    text=_('💬Mailing'), callback_data='send_to_all')
daily_joke_button = InlineKeyboardButton(text=_("🎭Joke of the day"),
                                         callback_data='daily_joke')
download_log_button = InlineKeyboardButton(text=_("📄View log"),
                                           callback_data='download_log')

admin_keyboard.row(add_joke_button)
admin_keyboard.row(send_to_all_button)
admin_keyboard.row(daily_joke_button)
admin_keyboard.row(download_log_button)

random_button = InlineKeyboardButton(_('🔀Random joke'),
                                     callback_data="random_joke")
random_keyboard = InlineKeyboardMarkup(row_width=2)
random_keyboard.add(random_button)

cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
cancel = KeyboardButton(_("↩️Cancel"))
cancel_keyboard.add(cancel)

lang_keyboard = InlineKeyboardMarkup()
lang_keyboard.add(InlineKeyboardButton(text="Українська🇺🇦", callback_data="lang_uk"),
                  InlineKeyboardButton(text="English🇬🇧", callback_data="lang_en"))


def return_rate_keyboard(joke_id):
    rate_keyboard = InlineKeyboardMarkup()
    like_button = InlineKeyboardButton(text='👍',
                                       callback_data=f'like_{joke_id}')
    dislike_button = InlineKeyboardButton(text='👎',
                                          callback_data=f'dislike_{joke_id}')
    rate_keyboard.row(like_button, dislike_button)
    return rate_keyboard


def return_rating_and_seen_keyboard(joke_rate, joke_id):
    rating_button = InlineKeyboardButton(text=_('📊Rating: {joke_rate}').format(joke_rate=joke_rate),
                                         callback_data='rating')
    seen_rating_button = InlineKeyboardButton(text=_('👀Viewed'),
                                              callback_data=f'seen_{joke_id}')

    rating_keyboard = InlineKeyboardMarkup()
    rating_keyboard.row(rating_button)
    rating_keyboard.row(seen_rating_button)
    return rating_keyboard


def return_seen_count_rate_keyboard(joke_seens, joke_id):
    hidden_seen_count_rate_button = InlineKeyboardButton(
        text=_("📊Joke rate"), callback_data=f"rating_{joke_id}")
    seen_count_button = InlineKeyboardButton(
        text=_('👀Viewed by: {joke_seens}').format(joke_seens=joke_seens), callback_data=f'seeen_{joke_id}')

    seen_count_rate_keyboard = InlineKeyboardMarkup()
    seen_count_rate_keyboard.row(hidden_seen_count_rate_button)
    seen_count_rate_keyboard.row(seen_count_button)
    return seen_count_rate_keyboard


def return_seen_rate_keyboard(joke_id):
    hidden_seen_rate_button = InlineKeyboardButton(
        text=_("📊Joke rate"), callback_data=f"rate_{joke_id}")
    seen_button = InlineKeyboardButton(text=_('👀Viewed'),
                                       callback_data=f'seen_{joke_id}')

    seen_rate_keyboard = InlineKeyboardMarkup()
    seen_rate_keyboard.row(hidden_seen_rate_button)
    seen_rate_keyboard.row(seen_button)
    return seen_rate_keyboard


def return_rating_keyboard(joke_rate):
    rate_button = InlineKeyboardButton(text=_('📊Rating: {joke_rate}').format(joke_rate=joke_rate),
                                       callback_data='rating')

    rating_keyboard = InlineKeyboardMarkup()
    rating_keyboard.row(rate_button)
    return rating_keyboard


def return_hidden_rating_keyboard(joke_id):
    hidden_rate_button = InlineKeyboardButton(
        text=_("📊Joke rate"), callback_data=f"rate_{joke_id}")

    hidden_rate_keyboard = InlineKeyboardMarkup()
    hidden_rate_keyboard.row(hidden_rate_button)
    return hidden_rate_keyboard
