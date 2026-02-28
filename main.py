import asyncio
import logging
import selectors
import sys
from zoneinfo import ZoneInfo

from aiocron import crontab
from aiogram.types import ErrorEvent

from app import bot, dp, get_bot_username, i18n, router
from config import BOT_COMMANDS, admin_id
from middlewares import My18nMiddleware, ThrottlingMiddleware, UserBannedMiddleware
from services import analytics, database

daily_joke_job = None


@router.error()
async def handle_errors(event: ErrorEvent):
    logging.error(
        "Update handling failed: %s",
        event.exception,
        exc_info=(type(event.exception), event.exception, event.exception.__traceback__),
    )


async def on_shutdown():
    try:
        await bot.send_message(admin_id, "Bot stopped.")
    except Exception:
        logging.exception("Failed to notify admin on shutdown")

    await analytics.close()
    await database.close()


async def on_startup():
    await database.connect()
    await analytics.initialize()
    await get_bot_username()

    try:
        await bot.send_message(admin_id, "Bot started.")
    except Exception:
        logging.exception("Failed to notify admin on startup")


async def main():
    from handlers import admin_router, daily_joke, user_router

    global daily_joke_job

    await bot.set_my_commands(commands=BOT_COMMANDS)
    await bot.delete_webhook(drop_pending_updates=True)

    dp.message.middleware(ThrottlingMiddleware())
    My18nMiddleware(i18n).setup(dp)
    dp.message.outer_middleware(UserBannedMiddleware())
    dp.callback_query.outer_middleware(UserBannedMiddleware())
    dp.inline_query.outer_middleware(UserBannedMiddleware())

    dp.include_routers(router, admin_router, user_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    daily_joke_job = crontab("0 12 * * *", func=daily_joke, start=True, tz=ZoneInfo("Europe/Kyiv"))

    await dp.start_polling(bot)


def create_event_loop():
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop(selectors.SelectSelector())

    return asyncio.new_event_loop()


if __name__ == "__main__":
    with asyncio.Runner(loop_factory=create_event_loop) as runner:
        runner.run(main())
