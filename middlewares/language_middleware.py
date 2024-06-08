from typing import Any, Dict, Optional

from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18nMiddleware, I18n


from services import DataBase

db = DataBase()


class My18nMiddleware(I18nMiddleware):
    def __init__(
            self,
            i18n: I18n,
            i18n_key: Optional[str] = "i18n",
            middleware_key: str = "i18n_middleware",
    ) -> None:
        super().__init__(i18n=i18n, i18n_key=i18n_key, middleware_key=middleware_key)

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:

        try:
            user_id = event.from_user.id
        except:
            user_id = None

        if user_id is not None:
            try:
                language = await db.get_language(user_id)
            except:
                language = None
        else:
            language = None

        return language if language is not None else self.i18n.default_locale
