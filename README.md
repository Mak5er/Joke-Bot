## Working Project link
<a href="https://www.python.org" target="_blank" rel="noreferrer"> <img src="https://quibtech.com/p/host-your-website-on-github/featuredImage_hu03ad3acbd1f4d769a3b53df03af47292_58966_1600x0_resize_box_3.png" alt="GitHub Pages" width="123" height="37"/></a>
    
    [GitHub Pages](https://mak5er.github.io/Joke-Bot/)
    [Telegram](https://t.me/makser_humor_bot)
    

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
