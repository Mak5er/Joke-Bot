import logging
import keep_alive

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import Config
from log.logger import custom_formatter

parse_mode = "Markdown"
bot = Bot(token=Config.token, parse_mode=parse_mode)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/bot_log.log")
handler.setFormatter(custom_formatter)

logger.addHandler(handler)

if __name__ == "__main__":
    from handlers import dp

    keep_alive.keep_alive()
    executor.start_polling(dp, skip_updates=True)
