import json
import hashlib

class User:
    def __init__(self):
        self.current_user = ""

        with open("users.json") as f:
            self.user_list = json.load(f)

    def save_user_data(self):
        with open("users.json", "w") as f:
            json.dump(self.user_list, f)

    def get_balance(self) -> int:
        '''returns the users balance in euros rounded to cents'''
        if self.current_user in self.user_list.keys():
            return round(self.user_list[self.current_user]["balance"] / 100, 2)
        return 0

    def set_user(self, username):
        if username in self.user_list.keys():
            self.current_user = username
            return True
        return False

    def unset_user(self):
        self.current_user = ""

    def exists(self, username):
        return username in self.user_list.keys()

    def check_password(self, password, username):
        if not self.exists(username):
            return False
        pwd_hash = hashlib.sha256()
        pwd_hash.update(password.encode("utf-8"))
        if pwd_hash.hexdigest() == self.user_list[username]["password"]:
            return True
        return False

    def change_password(self, current_pwd, new_pwd):
        current_pwd_hash = hashlib.sha256()
        current_pwd_hash.update(current_pwd.encode("utf-8"))

        new_pwd_hash = hashlib.sha256()
        new_pwd_hash.update(new_pwd.encode("utf-8"))

        if self.user_list[self.current_user]["password"] == current_pwd_hash.hexdigest():
            self.user_list[self.current_user]["password"] = new_pwd_hash.hexdigest()
            self.save_user_data()
            return True
        return False