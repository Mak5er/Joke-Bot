from flask import Flask
from threading import Thread
import time
from services import DataBase

db = DataBase()

app = Flask('')

import flask.cli

flask.cli.show_server_banner = lambda *args: None


@app.route('/')
def main():
    return '>>>print("Hello, world!")'


def run():
    app.run(host="0.0.0.0", port=10000)

def sleep():
    while True:
        time.sleep(60)
        return

def db_ping():
    while True:
        db.keep_alive()
        time.sleep(180)

def keep_alive():
    server = Thread(target=run)
    server.start()
    sleepServer = Thread(target=sleep)
    sleepServer.start()
    dbServer = Thread(target=db_ping)
    dbServer.start()