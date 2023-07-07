import asyncio
import logging

from aiogram import Bot, Dispatcher, executor
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

import keep_alive
from config import *
from log.logger import custom_formatter
from middlewares import setup_middleware

parse_mode = "Markdown"
bot = Bot(token=token, parse_mode=parse_mode)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

i18n = setup_middleware(dp)

_ = i18n.gettext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/bot_log.log")
handler.setFormatter(custom_formatter)

logger.addHandler(handler)


def rate_limit(limit: int, key=None):
    def decorator(func):
        setattr(func, 'throttling_rate_limit', limit)
        if key:
            setattr(func, 'throttling_key', key)
        return func

    return decorator


class ThrottlingMiddleware(BaseMiddleware):

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()

        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")

        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        try:
            await dispatcher.throttle(key, rate=limit)

        except Throttled as t:
            await self.message_throttled(message, t)
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):

        delta = throttled.rate - throttled.delta

        if throttled.exceeded_count <= 3:
            await message.reply(_('You send too many requests!'))

        await asyncio.sleep(delta)


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

    keep_alive.keep_alive()
    scheduler.start()
    dp.middleware.setup(ThrottlingMiddleware())
    executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown, on_startup=on_startup)
    asyncio.get_event_loop().run_forever()
