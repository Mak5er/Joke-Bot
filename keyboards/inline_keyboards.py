from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _


UI_TEXT = {
    "uk": {
        "random_joke": "🔀Випадковий анекдот",
        "select_category": "🔖Обрати категорію",
        "money": "💵Гроші",
        "family": "👨‍👩‍👦‍👦Родина",
        "blondes": "👱‍♀️Блондинки",
        "mother_in_law": "👵Теща",
        "school": "🏫Школа",
        "vovochka": "👦Вовочка",
        "medicine": "🏥Медицина",
        "students": "🎓Студенти",
        "work": "🏢Робота",
        "back": "🔙Назад",
        "update_rating": "🔃Оновити рейтинг",
        "viewed": "👀Переглянув",
        "feedback": "Зворотний зв'язок💬",
        "answer": "Відповісти💬",
    },
    "en": {
        "random_joke": "🔀Random joke",
        "select_category": "🔖Select category",
        "money": "💵Money",
        "family": "👨‍👩‍👦‍👦Family",
        "blondes": "👱‍♀️Blondes",
        "mother_in_law": "👵Mother-in-law",
        "school": "🏫School",
        "vovochka": "👦Vovochka",
        "medicine": "🏥Medicine",
        "students": "🎓Students",
        "work": "🏢Work",
        "back": "🔙Back",
        "update_rating": "🔃Update rating",
        "viewed": "👀Viewed",
        "feedback": "Feedback💬",
        "answer": "Answer💬",
    },
}


def _locale(user_locale: str | None) -> str:
    return user_locale if user_locale in UI_TEXT else "uk"


def _ui(key: str, user_locale: str | None) -> str:
    return UI_TEXT[_locale(user_locale)][key]


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


def random_keyboard(user_locale: str | None = None):
    buttons = [
        [InlineKeyboardButton(text=_ui("random_joke", user_locale), callback_data="random_joke")],
        [InlineKeyboardButton(text=_ui("select_category", user_locale), callback_data="select_category")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def category_keyboard(user_locale: str | None = None):
    buttons = [
        [
            InlineKeyboardButton(text=_ui("money", user_locale), callback_data="joke:про_гроші"),
            InlineKeyboardButton(text=_ui("family", user_locale), callback_data="joke:про_родину"),
        ],
        [InlineKeyboardButton(text=_ui("blondes", user_locale), callback_data="joke:про_білявок")],
        [
            InlineKeyboardButton(text=_ui("mother_in_law", user_locale), callback_data="joke:про_тещу"),
            InlineKeyboardButton(text=_ui("school", user_locale), callback_data="joke:про_школу"),
        ],
        [InlineKeyboardButton(text=_ui("vovochka", user_locale), callback_data="joke:про_вовочку")],
        [
            InlineKeyboardButton(text=_ui("medicine", user_locale), callback_data="joke:про_медицину"),
            InlineKeyboardButton(text=_ui("students", user_locale), callback_data="joke:про_студентів"),
        ],
        [InlineKeyboardButton(text=_ui("work", user_locale), callback_data="joke:про_роботу")],
        [InlineKeyboardButton(text=_ui("back", user_locale), callback_data="back_to_random")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard():
    kb = [[KeyboardButton(text=_("↩️Cancel"))]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def lang_keyboard():
    buttons = [[
        InlineKeyboardButton(text="Українська🇺🇦", callback_data="lang_uk"),
        InlineKeyboardButton(text="English🇬🇧", callback_data="lang_en"),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_rating_and_votes_keyboard(likes_count, dislikes_count, joke_id, user_vote, user_locale: str | None = None):
    like_button_text = f"☑️ 👍 {likes_count}" if user_vote == "like" else f"👍 {likes_count}"
    dislike_button_text = f"☑️ 👎 {dislikes_count}" if user_vote == "dislike" else f"👎 {dislikes_count}"

    buttons = [
        [
            InlineKeyboardButton(text=like_button_text, callback_data=f"like_{joke_id}"),
            InlineKeyboardButton(text=dislike_button_text, callback_data=f"dislike_{joke_id}"),
        ],
        [InlineKeyboardButton(text=_ui("update_rating", user_locale), callback_data=f"rating_{joke_id}")],
        [
            InlineKeyboardButton(text=_ui("random_joke", user_locale), callback_data="random_joke"),
            InlineKeyboardButton(text=_ui("select_category", user_locale), callback_data="select_category"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_rating_and_votes_keyboard_mailing(i18n, user_locale, likes_count, dislikes_count, joke_id, user_vote):
    like_button_text = f"☑️ 👍 {likes_count}" if user_vote == "like" else f"👍 {likes_count}"
    dislike_button_text = f"☑️ 👎 {dislikes_count}" if user_vote == "dislike" else f"👎 {dislikes_count}"

    buttons = [
        [
            InlineKeyboardButton(text=like_button_text, callback_data=f"like_{joke_id}"),
            InlineKeyboardButton(text=dislike_button_text, callback_data=f"dislike_{joke_id}"),
        ],
        [InlineKeyboardButton(text=_ui("update_rating", user_locale), callback_data=f"rating_{joke_id}")],
        [
            InlineKeyboardButton(text=_ui("random_joke", user_locale), callback_data="random_joke"),
            InlineKeyboardButton(text=_ui("select_category", user_locale), callback_data="select_category"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_rating_and_seen_keyboard(likes_count, dislikes_count, joke_id, user_locale: str | None = None):
    buttons = [
        [
            InlineKeyboardButton(text=f"👍 {likes_count}", callback_data=f"like_{joke_id}"),
            InlineKeyboardButton(text=f"👎 {dislikes_count}", callback_data=f"dislike_{joke_id}"),
        ],
        [InlineKeyboardButton(text=_ui("update_rating", user_locale), callback_data=f"rating_{joke_id}")],
        [InlineKeyboardButton(text=_ui("viewed", user_locale), callback_data=f"seen_{joke_id}")],
        [
            InlineKeyboardButton(text=_ui("random_joke", user_locale), callback_data="random_joke"),
            InlineKeyboardButton(text=_ui("select_category", user_locale), callback_data="select_category"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_back_keyboard():
    back_button = [[InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_list")]]
    return InlineKeyboardMarkup(inline_keyboard=back_button)


def return_search_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="ID", callback_data="search_id"),
            InlineKeyboardButton(text="Username", callback_data="search_username"),
        ],
        [InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def return_back_to_admin_keyboard():
    back_button = [[InlineKeyboardButton(text=_("🔙Back"), callback_data="back_to_admin")]]
    return InlineKeyboardMarkup(inline_keyboard=back_button)


def return_feedback_button(user_locale: str | None = None):
    feedback_button = [[InlineKeyboardButton(text=_ui("feedback", user_locale), callback_data="feedback")]]
    return InlineKeyboardMarkup(inline_keyboard=feedback_button)


def feedback_answer(feedback_message_id, feedback_message_chat_id, user_locale: str | None = None):
    answer_button = [[
        InlineKeyboardButton(
            text=_ui("answer", user_locale),
            callback_data=f"answer_{feedback_message_id}_{feedback_message_chat_id}",
        )
    ]]
    return InlineKeyboardMarkup(inline_keyboard=answer_button)
