![Joke-Bot](https://socialify.git.ci/Mak5er/Joke-Bot/image?description=1&font=Inter&language=1&name=1&pattern=Plus&theme=Auto)
# Python Joke-Bot

This code is a Python script for a Telegram bot. It utilizes the aiogram library for interacting with the Telegram Bot
API and includes various functionalities for handling user interactions, sending jokes, managing bans, and more.

### Functionality

- Handling various commands (e.g., /start, /language, /info, /help, /joke, /ping).
- Welcoming new chat members and updating user information.
- Allowing users to change their language preference.
- Sending random jokes or category-specific jokes.
- Handling user feedback and providing answers.
- Managing user bans and unbans.
- Admin functionality for viewing user information, exporting user data, and sending messages to all users.
- Scheduling daily joke messages using the apscheduler library.

### Installation

Clone the repository by running the following command:

    git clone https://github.com/Mak5er/Joke-Bot.git

Navigate to the cloned repository:

    cd Joke-Bot

Install the required Python packages using pip:

    pip install -r requirements.txt

Set up the necessary configuration by creating a  `.env`  file and defining the required variables:

`token` : Your Telegram bot token.
`admin_id` : The ID of the admin user.
`db_auth` : The authentication string for your PostgreSQL database.


Example  `.env`  file:

    token=YOUR_TELEGRAM_BOT_TOKEN
    admin_id=YOUR_ADMIN_USER_ID
    db_auth=YOUR_POSTGRESQL_AUTH_STRING


Set up a PostgreSQL database and update the  `db_auth`  variable in the  `.env`  file with the database authentication
string.

Run the script using Python:

    python main.py

Or using Docker:
    
    docker compose up -d

### Database Tables

The PostgreSQL database used by the bot includes the following tables:

- `users` : Stores user information, including user ID, username, chat type, language, status, and referrer ID.
- `sent_jokes` : Tracks jokes that have been sent to users, with references to the joke ID and user ID.
- `votes` : Stores user votes for jokes, with references to the joke ID, user ID, and vote type.
- `jokes_uk`  (and other language-specific joke tables): Contains jokes in different languages, with an ID, joke text,
  and tags.

### Usage

Once the bot is running, it will start listening for incoming messages and commands from users. Users can interact with
the bot by sending commands or engaging with the provided functionalities. The default language for conversation is
English, unless a specific language name is mentioned in the command.

Commands:

- /start : Start the conversation with the bot.
- /language : Change the language preference.
- /info : Get information about the bot.
- /help : Get help and usage instructions.
- /joke : Get a random joke.
- /ping : Check the bot's response time.

Users can also send feedback and the bot will provide answers.

### Telegram Bot Link

You can access the Telegram bot by clicking [here](https://t.me/AnekdotyRobot).

### Contributions

Contributions to this project are welcome. If you encounter any issues or have suggestions for improvements, please open
an issue or submit a pull request.

### License

This code is licensed under the [MIT License](https://opensource.org/licenses/MIT).

Feel free to modify and use this code for your own Telegram bot projects.
