from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
import logging

from config import I18N_DOMAIN, LOCALES_DIR
from services import DataBase

db = DataBase()


async def get_lang(user_id):
    try:
        language = await db.get_language(user_id)
        return language if language else 'uk'

    except Exception as e:
        logging.error(f"Error retrieving language for user {user_id}: {e}")
        return "en"


class ACLMiddleware(I18nMiddleware):
    async def get_user_locale(self, action, args):
        user = types.User.get_current()
        return await get_lang(user.id) or user.locale


def setup_lang_middleware(dp):
    i18n = ACLMiddleware(I18N_DOMAIN, LOCALES_DIR)
    dp.middleware.setup(i18n)
    return i18n
