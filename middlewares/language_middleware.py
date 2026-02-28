import logging
from typing import Any, Dict, Optional

from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18n, I18nMiddleware

from services import database

logger = logging.getLogger(__name__)


class My18nMiddleware(I18nMiddleware):
    def __init__(
        self,
        i18n: I18n,
        i18n_key: Optional[str] = "i18n",
        middleware_key: str = "i18n_middleware",
    ) -> None:
        super().__init__(i18n=i18n, i18n_key=i18n_key, middleware_key=middleware_key)

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        from_user = getattr(event, "from_user", None)
        if from_user is None:
            return self.i18n.default_locale

        try:
            language = await database.get_language(from_user.id)
        except Exception:
            logger.warning("Failed to resolve locale for user %s", from_user.id, exc_info=True)
            return self.i18n.default_locale

        return language or self.i18n.default_locale
