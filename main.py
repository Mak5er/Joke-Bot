from __future__ import annotations

import asyncio
import gettext

import betterlogging as logging
import httpx
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.filters import Command
from filters import ChatTypeF
from messages import bot_messages as bm
from aiogram.types import ErrorEvent

from config import *
from log.logger import custom_formatter
from middlewares import ConstI18nMiddleware, ThrottlingMiddleware
from services import DataBase

bot = Bot(token=token, parse_mode=ParseMode.HTML)
storage = RedisStorage.from_url("redis://localhost:6379/0")
dp = Dispatcher(storage=storage)
router = Router()

db = DataBase()

i18n = I18n(path=LOCALES_DIR, default_locale="en", domain="message")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/bot_log.log")
handler.setFormatter(custom_formatter)

logger.addHandler(handler)

logging.getLogger("werkzeug").disabled = True


async def send_analytics(user_id, user_lang_code, action_name):
    """
    Send record to Google Analytics
    """
    params = {
        'client_id': str(user_id),
        'user_id': str(user_id),
        'events': [{
            'name': action_name,
            'params': {
                'language': user_lang_code,
                "session_id": str(user_id),
                "engagement_time_msec": "100"

            }
        }],
    }
    async with httpx.AsyncClient() as client:
        await client.post(
            f'https://www.google-analytics.com/mp/collect?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}',
            json=params)


@router.message(Command('start'), ChatTypeF('private'))
async def start_cmd(msg: types.Message, i18n: I18n):
    name = msg.from_user.full_name
    await msg.answer(
        text=bm.welcome_message(name))

@router.error()
async def handle_errors(event: ErrorEvent):
    logging.error(f"Update: {event}\nException: {event.exception}")


async def on_shutdown():
    await bot.send_message(admin_id, "I'm stopped!")


async def on_startup():
    await bot.send_message(admin_id, "I'm launched!")


async def main():
    await bot.set_my_commands(commands=BOT_COMMANDS)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(router)
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.outer_middleware(ConstI18nMiddleware(locale="uk", i18n=i18n))
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.get_event_loop().run_forever()
