import sqlite3


class DataBase:

    def __init__(self, db_file):
        self.connect = sqlite3.connect(db_file)
        self.cursor = self.connect.cursor()

    async def add_users(self, user_id, user_name, user_username, chat_type):
        with self.connect:
            return self.cursor.execute(
                """INSERT OR IGNORE INTO users (user_id, user_name, user_username, chat_type) VALUES (?, ?, ?, ?)""",
                (user_id, user_name, user_username, chat_type))

    async def user_count(self):
        with self.connect:
            return self.cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    async def joke_count(self, table_name):
        with self.connect:
            return self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    async def sent_count(self):
        with self.connect:
            return self.cursor.execute("SELECT COUNT(*) FROM sent_jokes").fetchone()[0]

    async def joke_sent(self, user_id):
        with self.connect:
            return self.cursor.execute("SELECT COUNT(*) FROM sent_jokes WHERE user_id=(?)", (user_id,)).fetchone()[0]

    async def all_users(self):
        with self.connect:
            return self.cursor.execute("SELECT DISTINCT user_id FROM users").fetchall()

    async def get_private_users(self):
        with self.connect:
            return self.cursor.execute(
                "SELECT DISTINCT user_id FROM users WHERE chat_type = 'private' AND status != 'ban'").fetchall()

    async def add_joke(self, joke_text, table_name):
        with self.connect:
            return self.cursor.execute(f"INSERT INTO {table_name} (text) VALUES (?)", (joke_text,))

    async def seen_joke(self, joke_id, user_id):
        with self.connect:
            return self.cursor.execute("INSERT INTO sent_jokes (joke_id, user_id) VALUES (?, ?)", (joke_id, user_id))

    async def check_seen_joke(self, joke_id, user_id):
        with self.connect:
            return self.cursor.execute("SELECT * FROM sent_jokes WHERE joke_id = ? AND user_id = ?",
                                       (joke_id, user_id)).fetchone()

    async def joke_seens(self, joke_id):
        with self.connect:
            return self.cursor.execute("SELECT COUNT(*) FROM sent_jokes WHERE joke_id = ?", (joke_id,)).fetchone()[0]

    async def joke_rate(self, joke_id, table_name):
        with self.connect:
            return self.cursor.execute(f"SELECT rate FROM {table_name} WHERE id = ?", (joke_id,)).fetchone()[0]

    async def like_joke(self, joke_id, table_name):
        with self.connect:
            return self.cursor.execute(f"UPDATE {table_name} SET rate = rate + 1 WHERE id = ?", (joke_id,))

    async def dislike_joke(self, joke_id, table_name):
        with self.connect:
            return self.cursor.execute(f"UPDATE {table_name} SET rate = rate - 1 WHERE id = ?", (joke_id,))

    async def get_joke(self, user_id, table_name):
        with self.connect:
            return self.cursor.execute(
                f'SELECT * FROM {table_name} WHERE id NOT IN (SELECT joke_id FROM sent_jokes WHERE user_id = ?) AND rate = (SELECT MAX(rate) FROM {table_name} WHERE id NOT IN (SELECT joke_id FROM sent_jokes WHERE user_id = ?))ORDER BY RANDOM()',
                (user_id, user_id)).fetchall()

    async def get_language(self, user_id):
        with self.connect:
            return self.cursor.execute("SELECT DISTINCT language FROM users WHERE user_id=(?)",
                                       (user_id,)).fetchone()[0]

    async def set_language(self, user_id, language):
        with self.connect:
            return self.cursor.execute("UPDATE users SET language=(?) WHERE user_id=(?)", (language, user_id))

    async def status(self, user_id):
        with self.connect:
            return self.cursor.execute("SELECT DISTINCT status FROM users WHERE user_id = (?)", (user_id,)).fetchone()[
                0]

    async def get_admins(self):
        with self.connect:
            return self.cursor.execute("SELECT DISTINCT user_id FROM users WHERE status = admin", ).fetchall()

    async def get_user_info(self, user_id):
        with self.connect:
            return self.cursor.execute(
                "SELECT user_name, user_username, status FROM users WHERE user_id = (?)",
                (user_id,))

    async def get_user_info_username(self, user_username):
        with self.connect:
            return self.cursor.execute(
                "SELECT user_name, user_id, status FROM users WHERE user_username = (?)",
                (user_username,))

    async def ban_user(self, user_id):
        with self.connect:
            return self.cursor.execute("UPDATE users SET status=(?) WHERE user_id=(?)", ("ban", user_id))

    async def get_all_users_info(self):
        with self.connect:
            return self.cursor.execute(
                "SELECT user_id, chat_type, user_name, user_username, language, status FROM users").fetchall()

    async def unban_user(self, user_id):
        with self.connect:
            return self.cursor.execute("UPDATE users SET status=(?) WHERE user_id=(?)", ("user", user_id))
