import asyncio

import betterlogging as logging
import httpx
from aiogram import Bot, Dispatcher, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware

from config import *
from log.logger import custom_formatter

bot = Bot(token=token, parse_mode=ParseMode.HTML)
storage = RedisStorage.from_url("redis://localhost:6379/0")
dp = Dispatcher(storage=storage)
router = Router()

i18n = I18n(path="locales", default_locale="uk", domain="message")
i18n_middleware = SimpleI18nMiddleware(i18n=i18n)

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


@router.error()
async def handle_errors(update, exception):
    logging.error(f"Update: {update}\nException: {exception}")


async def on_shutdown():
    await bot.send_message(admin_id, _("I'm stopped!"))


async def on_startup():
    await bot.send_message(admin_id, _("I'm launched!"))


async def main():
    await bot.set_my_commands(commands=BOT_COMMANDS)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.get_event_loop().run_forever()
