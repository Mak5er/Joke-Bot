from typing import Any, Dict, Optional

from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18nMiddleware, I18n

from services import DataBase

db = DataBase()


class ConstI18nMiddleware(I18nMiddleware):
    def __init__(
            self,
            locale: str,
            i18n: I18n,
            i18n_key: Optional[str] = "i18n",
            middleware_key: str = "i18n_middleware",
    ) -> None:
        super().__init__(i18n=i18n, i18n_key=i18n_key, middleware_key=middleware_key)
        self.locale = locale
        print(locale)

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        print(self.locale)
        return self.locale
