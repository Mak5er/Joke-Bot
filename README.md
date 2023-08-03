## Project links
<a href="https://t.me/makser_humor_bot" target="_blank"> <img src="https://www.vectorlogo.zone/logos/telegram/telegram-tile.svg" alt="Telegram" width="60" height="60"/></a> 
<a href="https://mak5er.github.io/Joke-Bot/" target="_blank"> <img src="https://bischrob.github.io/images/githubpages/githubpages.jpeg" alt="GitHub Pages" width="65" height="60" style="border-radius: 10px;"></a> 
    

## Project description

This project is a Telegram bot that sends Ukrainian jokes to users. The bot is implemented using the Python programming language 
and uses the Aiogram framework to interact with the Telegram API.

## Usage

After successfully launching the program and connecting the bot to Telegram, you can run the following commands:

    /start - start interacting with the bot and receive a welcome message.
    /joke - get a random joke.
    /admin - access to the admin panel (only administrators are allowed).
    /info - get information about the user and statistics of bot usage.
    /help - get list of all commands.

## Functionality

### User

    Getting a random joke from the database.
    View the bot usage statistics.
    Can send feedback messages to bot.

### Administrator

    Adding new jokes to the database.
    Sending messages on behalf of the bot to all users.
    Ban/unban users from admin pannel.

### Bot
    Sending daily joke everyday by schedule

### keep_alive.py
    This file is used to track bot's activity.

## Database

The bot uses a SQLite database with the following tables:

    sent_jokes - stores the identifiers of jokes that have been sent to users.
    jokes - contains a list of jokes.
    users - stores the identifiers of users who use the bot.
