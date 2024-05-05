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
