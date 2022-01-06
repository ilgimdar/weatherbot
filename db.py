import sqlite3


class BotDB:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def user_exists(self, user_id):
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def get_user_id(self, user_id):
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def add_user(self, user_id):
        self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))
        return self.conn.commit()

    def add_city(self, user_id, city_name):
        self.cursor.execute("INSERT INTO `records` (`users_id`, `city`) VALUES (?, ?)",
                            (self.get_user_id(user_id), city_name))
        return self.conn.commit()

    def set_city(self, user_id, city_name):
        self.cursor.execute("UPDATE `records` SET `users_id` = ?, `city` = ?",
                            (self.get_user_id(user_id), city_name))
        return self.conn.commit()

    def get_city(self, user_id):
        result = self.conn.execute("SELECT `city` FROM `records` WHERE `users_id` = ?", (self.get_user_id(user_id),))
        return result.fetchall()

    def close(self):
        self.conn.close()
