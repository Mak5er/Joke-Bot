## Working Project link
    https://bit.ly/joke-bot

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

## Database

The bot uses a SQLite database with the following tables:

    sent_jokes - stores the identifiers of jokes that have been sent to users.
    jokes - contains a list of jokes.
    users - stores the identifiers of users who use the bot.
