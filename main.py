import asyncio
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import *
from log.logger import custom_formatter
from middlewares import setup_lang_middleware, setup_ban_middlewares, setup_throttling_middlewares

parse_mode = "Markdown"
bot = Bot(token=token, parse_mode=parse_mode)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

i18n = setup_lang_middleware(dp)

_ = i18n.gettext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/bot_log.log")
handler.setFormatter(custom_formatter)

logger.addHandler(handler)

logging.getLogger("werkzeug").disabled = True


@dp.errors_handler()
async def handle_errors(update, exception):
    logging.error(f"Update: {update}\nException: {exception}")


async def on_shutdown(dp):
    await bot.send_message(admin_id, _("I'm stopped!"))


async def on_startup(dp):
    await bot.send_message(admin_id, _("I'm launched!"))


if __name__ == "__main__":
    from handlers.admin import dp

    from handlers.user import dp, scheduler

    scheduler.start()
    setup_throttling_middlewares(dp)
    setup_ban_middlewares(dp)
    executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown, on_startup=on_startup)
    asyncio.get_event_loop().run_forever()
