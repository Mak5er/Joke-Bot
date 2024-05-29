from main import _


def welcome_message(name):
    return _("Hello <b>{name}</b>! I'm a bot with jokes.\n"
             "Full information on the bot /info\n"
             "List of commands /help").format(name=name)


def admin_panel(user_count, active_user_count, inactive_user_count, joke_count, sent_count):
    return _("""Hello, this is the admin panel.
    
🪪Number of bot users: <b>{user_count}</b>
📱Number of active users: <b>{active_user_count}</b>
📵Number of inactive users: <b>{inactive_user_count}</b>
🃏Number of jokes in the database: <b>{joke_count}</b>
📬Total number of jokes read: <b>{sent_count}</b>

Admin commands:
/ideas - list ideas from users
/get_users - download table with all users info
/system_info - get info about system""").format(user_count=user_count,
                                                active_user_count=active_user_count,
                                                inactive_user_count=inactive_user_count,
                                                joke_count=joke_count,
                                                sent_count=sent_count)


def admin_info(username, joke_sent, joke_count, sent_count, refs_count, ref_url):
    return _("""
Hello <b>{username}</b>! You are an administrator, to see more information and controls, please type /admin.

Statistics:
📁Number of jokes in the database: <b>{joke_count}</b>
📚Jokes read by you: <b>{joke_sent}</b>
📬Total number of jokes read by everyone: <b>{sent_count}</b>

Total referrals: <b>{refs_count}</b>
Your ref link: <a href="{ref_url}">{ref_url}</a>

Bot site - <a href="https://anekdoty.pp.ua">https://anekdoty.pp.ua</a>

<b>If you want to offer an anecdote or ask a question, click the Feedback💬 button!</b>""").format(username=username,
                                                                                                  joke_sent=joke_sent,
                                                                                                  joke_count=joke_count,
                                                                                                  sent_count=sent_count,
                                                                                                  refs_count=refs_count,
                                                                                                  ref_url=ref_url)


def user_info(username, joke_sent, joke_count, sent_count, refs_count, ref_url):
    return _('''
Hello <b>{username}</b>! I am a bot where you can read jokes.

Statistics:
📁Number of jokes in the database: <b>{joke_count}</b>
📚Jokes read by you: <b>{joke_sent}</b>
📬Total number of jokes read by everyone: <b>{sent_count}</b>

Total referrals: <b>{refs_count}</b>
Your ref link: <a href="{ref_url}">{ref_url}</a>

Bot site - <a href="https://anekdoty.pp.ua">https://anekdoty.pp.ua</a>

<b>If you want to offer an anecdote or ask a question, click the Feedback💬 button!</b>''').format(username=username,
                                                                                                  joke_sent=joke_sent,
                                                                                                  joke_count=joke_count,
                                                                                                  sent_count=sent_count,
                                                                                                  refs_count=refs_count,
                                                                                                  ref_url=ref_url)


def help_message():
    return _("""🤖 This is a bot with jokes. Here is a list of available commands:

️/start - start interacting with the bot
/joke - get a random joke
/info - get information about the bot
/find - find joke by id or text
/language - change language
""")


def joke_rating(joke_rate):
    return _("📊Rating: <b>{joke_rate}</b>").format(joke_rate=joke_rate)


def liked_joke():
    return _("You 👍 this!")


def disliked_joke():
    return _("You 👎 this!")


def revoked_vote():
    return _("You revoked your vote!")


def updated_rating():
    return _("🔃The rating is updated!")


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
    return _("<b>Joke of the day:</b>\n\n{joke_text}").format(joke_text=joke_text)


def dont_understood(name):
    return _("""<b>{name}</b>, I don't understand you! Type /help to get a list of commands!
    
<b>If you want to offer an anecdote or ask a question, click the Feedback💬 button!</b>""").format(name=name)


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
    return _("""Hi! Thank you for adding me to <b>'{chat_title}'</b>
For correct operation, please grant me administrator rights!
Type /help to get a list of commands""").format(chat_title=chat_title)


def please_choose():
    return _("Please choose your language!")


def choose_lan(language):
    if language == "uk":
        return """Ви обрали українську мову🇺🇦!
Ви завжди можете змінити мову написавши /language"""
    elif language == "en":
        return """You have selected English🇬🇧!
You can always change the language by writing /language"""


def return_user_info(user_name, user_id, user_username, status):
    return _("""<b>USER INFO</b>
<b>Name</b>: {user_name}
<b>ID</b>: {user_id}
<b>Username</b>: {user_username}
<b>Status</b>: {status}""").format(user_name=user_name, user_id=user_id, user_username=user_username, status=status)


def ban_message(reason):
    return _("🚫You have been banned, contact @mak5er for more information!\nReason: {reason}").format(reason=reason)


def unban_message():
    return _("🎉You have been unbanned!")


def successful_ban(banned_user_id):
    return _("User {banned_user_id} successfully banned!").format(banned_user_id=banned_user_id)


def successful_unban(unbanned_user_id):
    return _("User {unbanned_user_id} successfully unbanned!").format(unbanned_user_id=unbanned_user_id)


def feedback_message_send(user, feedback_message):
    return _("<b>New message</b> from user: <b>{user}</b>\n<b>Message:</b> <code>{feedback_message}</code>").format(
        user=user,
        feedback_message=feedback_message)


def pick_a_joke():
    return _("Pick a joke:")


def system_info(pc_info):
    return _("<b>System information:</b>\n\n{pc_info}").format(pc_info=pc_info)


def get_formatted_system_info(specs):
    system_info_template = _("""
<b>Operating System</b>: <i>{operating_system}</i>
<b>OS Version</b>: <i>{os_version}</i>
<b>Machine Name</b>: <i>{machine_name}</i>
<b>Processor Architecture</b>: <i>{processor_architecture}</i>
<b>Processor Model</b>: <i>{processor_model}</i>
<b>Physical Cores</b>: <i>{physical_cores}</i>
<b>Logical Cores</b>: <i>{logical_cores}</i>
<b>Total Memory</b>: <i>{total_memory:.2f}</i> MB
<b>Available Memory</b>: <i>{available_memory:.2f}</i> MB
<b>Memory Usage</b>: <i>{memory_usage}</i>%
""")
    formatted_info = system_info_template.format(**specs)
    return formatted_info


def search_user_by():
    return _('Search user by:')


def type_user(search):
    return _('Type user {search}:').format(search=search)


def action_canceled():
    return _('Action canceled!')


def your_message_sent():
    return _('Your message sent!')


def something_went_wrong():
    return _("Something went wrong, see log for more information!")


def any_ideas():
    return _("There are no ideas for you.")


def idea_deleted():
    return _("Idea deleted.")


def refferal_joined(user_id, refs_count):
    return _(
        "Referral <b>{user_id}</b> has registered at your invitation!\nTotal number of invitees: <b>{refs_count}</b>").format(
        user_id=user_id, refs_count=refs_count)


def please_enter_message():
    return _('Please enter your message:')


def your_message_sent_with_id(feedback_message_id):
    return _("Your message <b>{feedback_message_id}</b> sent!").format(feedback_message_id=feedback_message_id)


def select_category():
    return _('Please select category:')


def nothing_found():
    return _("Nothing was found.")


def type_joke_text_or_id():
    return _("Type joke text or ID:")
