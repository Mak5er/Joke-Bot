import psycopg2
import config

keepalive_kwargs = {
  "keepalives": 1,
  "keepalives_idle": 60,
  "keepalives_interval": 10,
  "keepalives_count": 5
}


class DataBase:

    def __init__(self):
        self.connect = psycopg2.connect(config.db_auth, **keepalive_kwargs)
        self.cursor = self.connect.cursor()

    def keep_alive(self):
        if self.connect is None:
            self.connect = psycopg2.connect(config.db_auth)
            self.cursor = self.connect.cursor()
            self.cursor.execute("SELECT 1")

    async def add_users(self, user_id, user_name, user_username, chat_type, language, status, referrer_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(
                    """INSERT INTO users (user_id, user_name, user_username, chat_type, language, status, referrer_id) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING;""",
                    (user_id, user_name, user_username, chat_type, language, status, referrer_id))
        except psycopg2.OperationalError as e:
            print(e)
            pass
            
    async def delete_user(self, user_id):        
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(
                    """DELETE FROM users WHERE user_id = %s;""",
                    (user_id,))
        except psycopg2.OperationalError as e:
            print(e)
            pass        

    async def user_count(self):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT COUNT(*) FROM users")
                return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def joke_count(self, table_name):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                return self.cursor.fetchone()[0]

        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def sent_count(self):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT COUNT(*) FROM sent_jokes")
                return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def joke_sent(self, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT COUNT(*) FROM sent_jokes WHERE user_id=%s", (user_id,))
                return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def all_users(self):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT user_id FROM users")
                return self.cursor.fetchall()
        
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def user_exist(self, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                return self.cursor.fetchall()
            
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def user_update_name(self, user_id, user_name, user_username):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("UPDATE users SET user_username=%s, user_name=%s WHERE user_id=%s",
                            (user_username, user_name, user_id))
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def get_private_users(self):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT DISTINCT user_id FROM users WHERE chat_type = 'private' AND status != 'ban'")
            return self.cursor.fetchall()
        except psycopg2.OperationalError as e:
            print(e)
            pass
        

    async def refs_count(self, referrer_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id=%s", (referrer_id,))
            return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def add_joke(self, joke_text, table_name):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(f"INSERT INTO {table_name} (text) VALUES (%s)", (joke_text,))
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def seen_joke(self, joke_id, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("INSERT INTO sent_jokes (joke_id, user_id) VALUES (%s, %s)", (joke_id, user_id))
        except psycopg2.OperationalError as e:
            print(e)
            pass
    async def check_seen_joke(self, joke_id, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT * FROM sent_jokes WHERE joke_id = %s AND user_id = %s", (joke_id, user_id))
                return self.cursor.fetchone()
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def joke_seens(self, joke_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT COUNT(*) FROM sent_jokes WHERE joke_id = %s", (joke_id,))
                return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def joke_rate(self, joke_id, table_name):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(f"SELECT rate FROM {table_name} WHERE id = %s", (joke_id,))
                return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass

    async def like_joke(self, joke_id, table_name):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(f"UPDATE {table_name} SET rate = rate + 1 WHERE id = %s", (joke_id,))
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def dislike_joke(self, joke_id, table_name):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(f"UPDATE {table_name} SET rate = rate - 1 WHERE id = %s", (joke_id,))
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def get_joke(self, user_id, table_name):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(
                    """
                    SELECT * FROM jokes_uk 
                    WHERE id NOT IN (SELECT joke_id FROM sent_jokes WHERE user_id = %s) 
                    ORDER BY (
                        SELECT COUNT(*) FROM votes WHERE joke_id = jokes_uk.id
                    ) DESC, 
                    RANDOM() 
                    LIMIT 1
                    """,
                    (user_id,)
                )
                return self.cursor.fetchall()
        
        except psycopg2.OperationalError as e:
            print(e)
            pass
        

    async def get_tagged_joke(self, user_id, tag):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(
                    """
                    SELECT * FROM jokes_uk 
                    WHERE id NOT IN (SELECT joke_id FROM sent_jokes WHERE user_id = %s) AND tags LIKE %s
                    ORDER BY (
                        SELECT COUNT(*) FROM votes WHERE joke_id = jokes_uk.id
                    ) DESC, 
                    RANDOM() 
                    LIMIT 1
                    """,
                    (user_id, f'%{tag}%'))
                return self.cursor.fetchall()
        except psycopg2.OperationalError as e:
            print(e)
            pass
        

    async def get_language(self, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT DISTINCT language FROM users WHERE user_id=%s", (user_id,))
                return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def get_tags(self, joke_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT tags FROM jokes_uk WHERE id = %s", (joke_id,))
                return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def set_language(self, user_id, language):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("UPDATE users SET language=%s WHERE user_id=%s", (language, user_id))
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def status(self, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT DISTINCT status FROM users WHERE user_id = %s", (user_id,))
                return self.cursor.fetchone()[0]
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def get_admins(self):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT DISTINCT user_id FROM users WHERE status = admin", )
                return self.cursor.fetchall()
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def get_user_info(self, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(
                    "SELECT user_name, user_username, status FROM users WHERE user_id = %s",
                    (user_id,))
                return self.cursor.fetchone()
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def get_user_info_username(self, user_username):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(
                    "SELECT user_name, user_id, status FROM users WHERE user_username = %s",
                    (user_username,))
                return self.cursor.fetchone()
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def ban_user(self, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("UPDATE users SET status=%s WHERE user_id=%s", ("ban", user_id))
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def get_all_users_info(self):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT user_id, chat_type, user_name, user_username, language, status FROM users")
                return self.cursor.fetchall()
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def unban_user(self, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("UPDATE users SET status=%s WHERE user_id=%s", ("user", user_id))
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def add_vote(self, joke_id, user_id, vote_type):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("INSERT INTO votes (joke_id, user_id, vote_type) VALUES (%s, %s, %s)",(joke_id, user_id, vote_type))
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def remove_vote(self, joke_id, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("DELETE FROM votes WHERE joke_id = %s AND user_id = %s",(joke_id, user_id))
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def update_vote(self, joke_id, user_id, new_vote_type):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("UPDATE votes SET vote_type = %s WHERE joke_id = %s AND user_id = %s",(new_vote_type, joke_id, user_id))
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def get_user_vote(self, joke_id, user_id):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute("SELECT vote_type FROM votes WHERE joke_id = %s AND user_id = %s",(joke_id, user_id))
                result = self.cursor.fetchone()
                if result:
                    return result[0]
                else:
                    return None
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
    async def count_votes(self, joke_id, vote_type):
        try:
            if self.connect is None:
                self.connect = psycopg2.connect(config.db_auth)
                self.cursor = self.connect.cursor()

            with self.connect:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM votes WHERE joke_id = %s AND vote_type = %s",
                    (joke_id, vote_type)
                )
                result = self.cursor.fetchone()
                if result:
                    return result[0]
                else:
                    return 0
        except psycopg2.OperationalError as e:
            print(e)
            pass
        
