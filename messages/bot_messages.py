def welcome_message(name):
    return f"""Привіт *{name}*! Я бот з анекдотами. 
Повна інформація по боту /info
Список команд /help"""


def admin_panel(user_count, joke_count, sent_count):
    return f'''Привіт! Це панель адміністратора.
🪪Кількість користувачів бота: *{user_count}*
🃏Кількість анекдотів в базі: *{joke_count}*
📬Всіма прочитано анекдотів: *{sent_count}*
'''


def admin_info(username, joke_sent, joke_count, sent_count):
    return f"""
Привіт *{username}*! Ви є адміністратором, щоб побачити більше інформації та елементи контролю пропишіть /admin.

Статистика:
📁Кількість анекдотів в базі: *{joke_count}*
📚Вами прочитано анекдотів: *{joke_sent}*
📬Всіма прочитано анекдотів: *{sent_count}*

Щоб запросити друга перейдіть або перешліть йому це посилання - https://cutt.ly/qwr2PFSE

Бот знаходиться в стадії розробки тому можливі баги і неполадки!
Для скарг і пропозицій писати - @mak5er"""


def user_info(username, joke_sent, joke_count, sent_count):
    return f"""Привіт *{username}*! Я бот в якому ти можеш прочитати українські анекдоти.

Статистика:
📁Кількість анекдотів в базі: *{joke_count}*
📚Вами прочитано анекдотів: *{joke_sent}*
📬Всіма прочитано анекдотів: *{sent_count}*

Щоб запросити друга перейдіть або перешліть йому це посилання - https://cutt.ly/qwr2PFSE

*Наразі бот не має можливості оцінки анекотів в групі, тому якщо ви хочете оцінювати анекдоти після прочитання - 
читайте їх в особистому чаті з ботом.*

*Бот знаходиться в стадії розробки тому можливі баги і неполадки!
Для скарг і пропозицій писати - @mak5er*"""


def help_message():
    return """🤖 Це бот з анекдотами. Ось список доступних команд:

️/start - почати взаємодію з ботом
/joke - отримати випадковий анекдот
/info - отримати інформацію про бота

Команда /start використовується для початку взаємодії з ботом. Після відправлення цієї команди, бот буде готовий приймати інші команди від користувача.

Команда /joke дозволяє отримати випадковий анекдот від бота. При виклику цієї команди, бот буде відповідати випадково вибраним анекдотом.

Команда /info дозволяє отримати інформацію про бота. Тут можна переглянути статистику бота, інформацію про розробника і посилання для запрошення друга."""


def joke_rating(joke_rate):
    return f"📊Рейтинг анекдота: {joke_rate}"


def liked_joke():
    return "Ви проголосували за анекдот!"


def disliked_joke():
    return "Ви проголосували проти анекдота!"


def seen_joke():
    return "Ви відмітили цей анекдот як прочитаний!"


def already_seen_joke():
    return "Ви вже відмічали цей анекдот як прочитаний!"


def finish_mailing():
    return "Розсилку завершено!"


def start_mailing():
    return "Починаю розсилку..."

def prees_button():
    return "Натисни на кнопку, щоб отримати анекдот."

def all_send():
    return 'На жаль, всі анекдоти вже були надіслані вам.'
