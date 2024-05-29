from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from main import _

from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_keyboard():
    buttons = [
        [InlineKeyboardButton(text=_('📝Add a joke'), callback_data='add_joke')],
        [
            InlineKeyboardButton(text=_('💬Mailing'), callback_data='send_to_all'),
            InlineKeyboardButton(text=_("🎭Joke of the day"), callback_data='daily_joke')
        ],
        [
            InlineKeyboardButton(text=_("📄View log"), callback_data='download_log'),
            InlineKeyboardButton(text=_("❌📄Delete log"), callback_data='delete_log')
        ],
        [InlineKeyboardButton(text=_("👤Control User"), callback_data='control_user')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return keyboard


def random_keyboard():
    buttons = [
        [InlineKeyboardButton(text=_('🔀Random joke'), callback_data="random_joke")],
        [InlineKeyboardButton(text=_('🔖Select category'), callback_data="select_category")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def category_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text=_('💵Money'), callback_data="joke:про_гроші"),
            InlineKeyboardButton(text=_('👨‍👩‍👦‍👦Family'), callback_data="joke:про_родину"),
        ],
        [InlineKeyboardButton(text=_('👱‍♀️Blondes'), callback_data="joke:про_білявок")],
        [
            InlineKeyboardButton(text=_('👵Mother-in-law'), callback_data="joke:про_тещу"),
            InlineKeyboardButton(text=_('🏫School'), callback_data="joke:про_школу"),
        ],
        [InlineKeyboardButton(text=_('👦Vovochka'), callback_data="joke:про_вовочку")],
        [
            InlineKeyboardButton(text=_('🏥Medicine'), callback_data="joke:про_медицину"),
            InlineKeyboardButton(text=_('🎓Students'), callback_data="joke:про_студентів"),
        ],
        [InlineKeyboardButton(text=_('🏢Work'), callback_data="joke:про_роботу")],
        [InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_random")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def cancel_keyboard():
    kb = [
        [KeyboardButton(text=_("↩️Cancel"))]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard


def lang_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Українська🇺🇦", callback_data="lang_uk"),
            InlineKeyboardButton(text="English🇬🇧", callback_data="lang_en")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote):
    like_button_text = f'☑️ 👍 {likes_count}' if user_vote == 'like' else f'👍 {likes_count}'
    dislike_button_text = f'☑️ 👎 {dislikes_count}' if user_vote == 'dislike' else f'👎 {dislikes_count}'

    buttons = [
        [
            InlineKeyboardButton(text=like_button_text, callback_data=f'like_{joke_id}'),
            InlineKeyboardButton(text=dislike_button_text, callback_data=f'dislike_{joke_id}')
        ],
        [InlineKeyboardButton(text=_('🔃Update rating'), callback_data=f'rating_{joke_id}')]

    ]

    rating_and_votes_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return rating_and_votes_keyboard


# Клавіатура для груп з додатковою кнопкою "Переглянути"
def return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id):
    buttons = [
        [
            InlineKeyboardButton(text=f'👍 {likes_count}', callback_data=f'like_{joke_id}'),
            InlineKeyboardButton(text=f'👎 {dislikes_count}', callback_data=f'dislike_{joke_id}')
        ],
        [InlineKeyboardButton(text=_('🔃Update rating'), callback_data=f'rating_{joke_id}')],
        [InlineKeyboardButton(text=_('👀Viewed'), callback_data=f'seen_{joke_id}')]
    ]

    rating_and_seen_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return rating_and_seen_keyboard


def return_back_keyboard():
    back_button = [
        [InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_list")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=back_button)
    return keyboard


def return_search_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="ID", callback_data="search_id"),
            InlineKeyboardButton(text="Username", callback_data="search_username")
        ],
        [InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")]
    ]
    search_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return search_keyboard


def return_back_to_admin_keyboard():
    back_button = [
        [(InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin"))]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=back_button)
    return keyboard


def return_feedback_button():
    feedback_button = [
        [InlineKeyboardButton(text=_("Feedback💬"), callback_data='feedback')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=feedback_button)
    return keyboard


def feedback_answer(feedback_message_id, feedback_message_chat_id):
    answer_button = [
        [InlineKeyboardButton(text=_("Answer💬"),
                              callback_data=f'answer_{feedback_message_id}_{feedback_message_chat_id}')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=answer_button)
    return keyboard