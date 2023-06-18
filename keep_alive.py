from flask import Flask, render_template
import telebot
import config
from threading import Thread

app = Flask('')
bot = telebot.TeleBot(config.TOKEN)


@app.route('/')
def main():
    return render_template('index.html')


def run():
    app.run(host="0.0.0.0", port=8080)  # don't touch this


def keep_alive():
    server = Thread(target=run)
    server.start()
