import logging

from aiogram import types
from aiogram.utils.i18n import I18nMiddleware

from config import I18N_DOMAIN, LOCALES_DIR
from services import DataBase

db = DataBase()


async def get_lang(user_id):
    try:
        language = await db.get_language(user_id)
        return language if language else 'uk'

    except Exception as e:
        logging.error(f"Error retrieving language for user {user_id}: {e}")
        return "en"

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        if Locale is None:  # pragma: no cover
            raise RuntimeError(
                f"{type(self).__name__} can be used only when Babel installed\n"
                "Just install Babel (`pip install Babel`) "
                "or aiogram with i18n support (`pip install aiogram[i18n]`)"
            )

        event_from_user: Optional[User] = data.get("event_from_user", None)
        if event_from_user is None or event_from_user.language_code is None:
            return self.i18n.default_locale
        try:
            locale = Locale.parse(event_from_user.language_code, sep="-")
        except UnknownLocaleError:
            return self.i18n.default_locale

        if locale.language not in self.i18n.available_locales:
            return self.i18n.default_locale
        return locale.language