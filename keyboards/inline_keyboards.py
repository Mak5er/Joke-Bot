from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _


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
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def random_keyboard():
    buttons = [
        [InlineKeyboardButton(text=_('🔀Random joke'), callback_data="random_joke")],
        [InlineKeyboardButton(text=_('🔖Select category'), callback_data="select_category")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def lang_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Українська🇺🇦", callback_data="lang_uk"),
            InlineKeyboardButton(text="English🇬🇧", callback_data="lang_en")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote):
    like_button_text = f'☑️ 👍 {likes_count}' if user_vote == 'like' else f'👍 {likes_count}'
    dislike_button_text = f'☑️ 👎 {dislikes_count}' if user_vote == 'dislike' else f'👎 {dislikes_count}'

    buttons = [
        [
            InlineKeyboardButton(text=like_button_text, callback_data=f'like_{joke_id}'),
            InlineKeyboardButton(text=dislike_button_text, callback_data=f'dislike_{joke_id}')
        ],
        [InlineKeyboardButton(text=_('🔃Update rating'), callback_data=f'rating_{joke_id}')],
        [
            InlineKeyboardButton(text=_('🔀Random joke'), callback_data="random_joke"),
            InlineKeyboardButton(text=_('🔖Select category'), callback_data="select_category")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_rating_and_votes_keyboard_mailing(i18n, user_locale, likes_count, dislikes_count, joke_id, user_vote):
    i18n.context = i18n
    with i18n.use_locale(user_locale):
        like_button_text = f'☑️ 👍 {likes_count}' if user_vote == 'like' else f'👍 {likes_count}'
        dislike_button_text = f'☑️ 👎 {dislikes_count}' if user_vote == 'dislike' else f'👎 {dislikes_count}'

        buttons = [
            [
                InlineKeyboardButton(text=like_button_text, callback_data=f'like_{joke_id}'),
                InlineKeyboardButton(text=dislike_button_text, callback_data=f'dislike_{joke_id}')
            ],
            [InlineKeyboardButton(text=_('🔃Update rating'), callback_data=f'rating_{joke_id}')],
            [
                InlineKeyboardButton(text=i18n.gettext('🔀Random joke'), callback_data='random_joke'),
                InlineKeyboardButton(text=i18n.gettext('🔖Select category'), callback_data='select_category')
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id):
    buttons = [
        [
            InlineKeyboardButton(text=f'👍 {likes_count}', callback_data=f'like_{joke_id}'),
            InlineKeyboardButton(text=f'👎 {dislikes_count}', callback_data=f'dislike_{joke_id}')
        ],
        [InlineKeyboardButton(text=_('🔃Update rating'), callback_data=f'rating_{joke_id}')],
        [InlineKeyboardButton(text=_('👀Viewed'), callback_data=f'seen_{joke_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_back_keyboard():
    back_button = [
        [InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=back_button)


def return_search_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="ID", callback_data="search_id"),
            InlineKeyboardButton(text="Username", callback_data="search_username")
        ],
        [InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_back_to_admin_keyboard():
    back_button = [
        [(InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin"))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=back_button)


def return_feedback_button():
    feedback_button = [
        [InlineKeyboardButton(text=_("Feedback💬"), callback_data='feedback')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=feedback_button)


def feedback_answer(feedback_message_id, feedback_message_chat_id):
    answer_button = [
        [InlineKeyboardButton(text=_("Answer💬"),
                              callback_data=f'answer_{feedback_message_id}_{feedback_message_chat_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=answer_button)
