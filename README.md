## Project links
<a href="https://t.me/makser_humor_bot" target="_blank"> <img src="https://www.vectorlogo.zone/logos/telegram/telegram-tile.svg" alt="Telegram" width="60" height="60"/></a> 
<a href="https://mak5er.github.io/Joke-Bot/" target="_blank"> <img src="https://theaveragenz.com/wp-content/uploads/2021/07/3uy5od7tw2jf4fh7ldlv-800x400.jpeg" style="border-radius: 24px;" alt="GitHub Pages" width="120" height="60"/></a> 
    

## Project description

This project is a Telegram bot that sends Ukrainian jokes to users. The bot is implemented using the Python programming language
programming language and uses the Telebot framework to interact with the Telegram API.

## Usage

After successfully launching the program and connecting the bot to Telegram, you can run the following commands:

    /start - start interacting with the bot and receive a welcome message.
    /joke - get a random joke.
    /admin - access to the admin panel (only administrators are allowed).
    /info - get information about the user and statistics of bot usage.

## Functionality

### User

    Getting a random joke from the database.
    View the bot usage statistics.

### Administrator

    Adding new jokes to the database.
    Sending messages on behalf of the bot to all users.

### Bot
    Sending daily joke everyday by schedule

### keep_alive.py
    This file is designed to maintain free online hosting using the UptimeRobot service, which sends a request every 5 minutes.

## Database

The bot uses a SQLite database with the following tables:

    sent_jokes - stores the identifiers of jokes that have been sent to users.
    jokes - contains a list of jokes.
    users - stores the identifiers of users who use the bot.
