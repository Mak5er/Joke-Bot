from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

admin_keyboard = InlineKeyboardMarkup()
add_joke_button = InlineKeyboardButton(text='📝Додати анекдот',
                                       callback_data='add_joke')
send_to_all_button = InlineKeyboardButton(
    text='💬Повідомлення від імені бота', callback_data='send_to_all')
daily_joke_button = InlineKeyboardButton(text="🎭Анекдот дня",
                                         callback_data='daily_joke')
download_log_button = InlineKeyboardButton(text="📄Переглянути лог",
                                           callback_data='download_log')

admin_keyboard.row(add_joke_button)
admin_keyboard.row(send_to_all_button)
admin_keyboard.row(daily_joke_button)
admin_keyboard.row(download_log_button)

random_button = InlineKeyboardButton('🔀Рандомний анекдот',
                                     callback_data="random_joke")
random_keyboard = InlineKeyboardMarkup(row_width=2)
random_keyboard.add(random_button)


def return_rate_keyboard(joke_id):
    rate_keyboard = InlineKeyboardMarkup()
    like_button = InlineKeyboardButton(text='👍',
                                       callback_data=f'like_{joke_id}')
    dislike_button = InlineKeyboardButton(text='👎',
                                          callback_data=f'dislike_{joke_id}')
    rate_keyboard.row(like_button, dislike_button)
    return rate_keyboard


def return_rating_and_seen_keyboard(joke_rate, joke_id):
    rating_button = InlineKeyboardButton(text=f'📊Рейтинг: {joke_rate}',
                                         callback_data='rating')
    seen_rating_button = InlineKeyboardButton(text=f'👀Переглянув',
                                              callback_data=f'seen_{joke_id}')

    rating_keyboard = InlineKeyboardMarkup()
    rating_keyboard.row(rating_button)
    rating_keyboard.row(seen_rating_button)
    return rating_keyboard


def return_seen_count_rate_keyboard(joke_seens, joke_id):
    hidden_seen_count_rate_button = InlineKeyboardButton(
        text=f"📊Рейтинг анекдота", callback_data=f"rating_{joke_id}")
    seen_count_button = InlineKeyboardButton(
        text=f'👀Переглянуло: {joke_seens}', callback_data=f'seeen_{joke_id}')

    seen_count_rate_keyboard = InlineKeyboardMarkup()
    seen_count_rate_keyboard.row(hidden_seen_count_rate_button)
    seen_count_rate_keyboard.row(seen_count_button)
    return seen_count_rate_keyboard


def return_seen_rate_keyboard(joke_id):
    hidden_seen_rate_button = InlineKeyboardButton(
        text=f"📊Рейтинг анекдота", callback_data=f"rate_{joke_id}")
    seen_button = InlineKeyboardButton(text=f'👀Переглянув',
                                       callback_data=f'seen_{joke_id}')

    seen_rate_keyboard = InlineKeyboardMarkup()
    seen_rate_keyboard.row(hidden_seen_rate_button)
    seen_rate_keyboard.row(seen_button)
    return seen_rate_keyboard


def return_rating_keyboard(joke_rate):
    rate_button = InlineKeyboardButton(text=f'📊Рейтинг: {joke_rate}',
                                       callback_data='rating')

    rating_keyboard = InlineKeyboardMarkup()
    rating_keyboard.row(rate_button)
    return rating_keyboard


def return_hidden_rating_keyboard(joke_id):
    hidden_rate_button = InlineKeyboardButton(
        text=f"📊Рейтинг анекдота", callback_data=f"rate_{joke_id}")

    hidden_rate_keyboard = InlineKeyboardMarkup()
    hidden_rate_keyboard.row(hidden_rate_button)
    return hidden_rate_keyboard
