import os
from pathlib import Path

from aiogram.types import BotCommand
from dotenv import load_dotenv

load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value

    raise RuntimeError(f"Missing required environment variable: {name}")


BASE_DIR = Path(__file__).resolve().parent

token = get_required_env("token")
admin_id = int(get_required_env("admin_id"))
db_auth = get_required_env("db_auth")
MEASUREMENT_ID = os.getenv("MEASUREMENT_ID")
API_SECRET = os.getenv("API_SECRET")

DEFAULT_LOCALE = "uk"
DEFAULT_PRIVATE_CHAT_TYPE = "private"
DEFAULT_PUBLIC_CHAT_TYPE = "public"
DEFAULT_USER_STATUS = "active"
JOKES_TABLE = "jokes_uk"

BOT_COMMANDS = [
    {'command': 'start', 'description': '🚀Початок роботи / Get started 🔥'},
    {'command': 'joke', 'description': '🃏Читати анекдот / Read the joke 😂'},
    {'command': 'info', 'description': 'ℹ️Інформація про бота / Info about the bot 🤖'},
    {'command': 'find', 'description': '🔎Шукати анекдот /  Search for a joke 🔍'},
    {'command': 'language', 'description': '🇺🇦Змінити мову / change language 🇬🇧'},
    {'command': 'help', 'description': '❓Допомога з ботом / Help with the bot 🗂'},
]

ADMINS_UID = {admin_id}
