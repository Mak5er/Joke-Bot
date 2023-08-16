from main import _


def welcome_message(name):
    return _("Hello *{name}*! I'm a bot with jokes.\n"
             "Full information on the bot /info\n"
             "List of commands /help").format(name=name)


def admin_panel(user_count, joke_count, sent_count):
    return _("""Hello, this is the admin panel.
🪪Number of bot users: *{user_count}*
🃏Number of jokes in the database: *{joke_count}*
📬Total number of jokes read: *{sent_count}*

Admin commands:
/download\_db - download database
/del\_log - delete the log
/get\_users - download table with all users info
/system\_info - get info about system""").format(user_count=user_count,
                                                 joke_count=joke_count,
                                                 sent_count=sent_count)


def admin_info(username, joke_sent, joke_count, sent_count):
    return _("""
Hello *{username}*! You are an administrator, to see more information and controls, please type /admin.

Statistics:
📁Number of jokes in the database: *{joke_count}*.
📚Jokes read by you: *{joke_sent}*
📬Total number of jokes read by everyone: *{sent_count}*

Bot site - bit.ly/anekdotyky

*If you want to offer an anecdote or ask a question, click the Feedback💬 button!*

*The bot is under development, so bugs and malfunctions are possible!
For complaints and suggestions, write - @mak5er*""").format(username=username, joke_sent=joke_sent,
                                                            joke_count=joke_count,
                                                            sent_count=sent_count)


def user_info(username, joke_sent, joke_count, sent_count):
    return _('''
Hello *{username}*! I am a bot where you can read jokes.

Statistics:
📁Number of jokes in the database: *{joke_count}*.
📚Jokes read by you: *{joke_sent}*
📬Total number of jokes read by everyone: *{sent_count}*

Bot site - bit.ly/anekdotyky

*If you want to offer an anecdote or ask a question, click the Feedback💬 button!*

*The bot is under development, so bugs and malfunctions are possible!
For complaints and suggestions, write - @mak5er*''').format(username=username, joke_sent=joke_sent,
                                                            joke_count=joke_count,
                                                            sent_count=sent_count)


def help_message():
    return _("""🤖 This is a bot with jokes. Here is a list of available commands:

️/start - start interacting with the bot
/joke - get a random joke
/info - get information about the bot

The /start command is used to start interacting with the bot. After sending this command, the bot will be ready to accept other commands from the user.

The /joke command allows you to get a random joke from the bot. When this command is called, the bot will respond with a randomly selected joke.

The /info command allows you to get information about the bot. Here you can view bot statistics, information about the developer, and a link to invite a friend.""")


def joke_rating(joke_rate):
    return _("📊Rating: {joke_rate}").format(joke_rate=joke_rate)


def liked_joke():
    return _("You voted for the joke!")


def disliked_joke():
    return _("You voted against the joke!")


def seen_joke():
    return _("You have marked this joke as read!")


def already_seen_joke():
    return _("You have already marked this joke as read!")


def finish_mailing():
    return _("Mailing is complete!")


def start_mailing():
    return _("Starting mailing...")


def pres_button():
    return _("Click the button to get the joke.")


def all_send():
    return _('Unfortunately, all the jokes have already been sent to you.')


def daily_joke(joke_text):
    return _("*Joke of the day:*\n\n{joke_text}").format(joke_text=joke_text)


def dont_understood(name):
    return _("""*{name}*, I don't understand you! Type /help to get a list of commands!
*If you want to offer an anecdote or ask a question, click the Feedback💬 button!*""").format(name=name)


def not_groups():
    return _("This command cannot be used in a group!")


def log_deleted():
    return _("Log deleted, starting to write a new one.")


def mailing_message():
    return _('Enter the message to send:')


def canceled():
    return _("Action canceled")


def new_joke():
    return _("Enter a new joke:")


def joke_added():
    return _("The anecdote is given to the database.")


def join_group(chat_title):
    return _("""Hi! Thank you for adding me to *'{chat_title}'* 
For correct operation, please grant me administrator rights!""").format(chat_title=chat_title)


def please_choose():
    return _("Please choose your language!")


def choose_lan(language):
    if language == "uk":
        return """Ви обрали українську мову🇺🇦!
Ви завжди можете змінити мову написавши /language
"""
    elif language == "en":
        return """You have selected English🇬🇧!
You can always change the language by writing /language
"""


def return_user_info(user_name, user_id, user_username, status):
    return _("""*USER INFO*
_Name_: *{user_name}*
_ID_: *{user_id}*
_Username_: *{user_username}*
_Status_: *{status}*""").format(user_name=user_name, user_id=user_id, user_username=user_username, status=status)


def ban_message(reason):
    return _("🚫You have been banned, contact @mak5er for more information!\nReason: {reason}").format(reason=reason)


def unban_message():
    return _("🎉You have been unbanned!")


def successful_ban(banned_user_id):
    return _("User {banned_user_id} successfully banned!").format(banned_user_id=banned_user_id)


def successful_unban(unbanned_user_id):
    return _("User {unbanned_user_id} successfully unbanned!").format(unbanned_user_id=unbanned_user_id)


def feedback_message_send(user, feedback_message):
    return _("*New message* from user: *{user}*\n*Message:* `{feedback_message}`").format(user=user,
                                                                                          feedback_message=feedback_message)
