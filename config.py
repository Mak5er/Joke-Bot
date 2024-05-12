import os

from dotenv import load_dotenv

load_dotenv()
from pathlib import Path

token = str(os.getenv("token"))
admin_id = int(os.getenv("admin_id"))
db_auth = str(os.getenv("db_auth"))
MEASUREMENT_ID = str(os.getenv("MEASUREMENT_ID"))
API_SECRET = str(os.getenv("API_SECRET"))

I18N_DOMAIN = 'jokebot'
BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / 'locales'

BOT_COMMANDS = [
    {'command': 'start', 'description': '🚀Початок роботи / Getting started 🔥'},
    {'command': 'joke', 'description': '🃏Читати анекдот / Read the joke 😂'},
    {'command': 'info', 'description': 'ℹ️Інформація про бота / Info about the bot 🤖'},
    {'command': 'find', 'description': '🔎Шукати анекдот /  Search for a joke 🔍'},
    {'command': 'language', 'description': '🇺🇦Змінити мову / change language 🇬🇧'},
    {'command': 'help', 'description': '❓Допомога з ботом / Help with the bot 🗂'},
]

ADMINS_UID = [admin_id]

