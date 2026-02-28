import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.i18n import I18n

import log.logger
from config import BASE_DIR, DEFAULT_LOCALE, token
from services import analytics

default = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=token, default=default)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
i18n = I18n(path=BASE_DIR / "locales", default_locale=DEFAULT_LOCALE, domain="messages")
bot_username: str | None = None

logger = logging.getLogger(__name__)
logging.getLogger("werkzeug").disabled = True


async def send_analytics(user_id: int, user_lang_code: str | None, action_name: str) -> None:
    analytics.queue_event(user_id=user_id, user_lang_code=user_lang_code, action_name=action_name)


async def get_bot_username() -> str:
    global bot_username

    if bot_username is None:
        bot_username = (await bot.get_me()).username

    return bot_username
