import json
import hashlib
import os.path
from json import JSONDecodeError

from logs.log import log_message

DEFAULT_FILE = "users.dat"


def generate_hash_key(password: str) -> str:
    hash_key = hashlib.sha256()
    hash_key.update(password.encode("utf-8"))
    return hash_key.hexdigest()


class Database:

    def __init__(self, save_file: str = DEFAULT_FILE):
        self.save_file = save_file
        self.create_file()

    def create_file(self):
        if not os.path.exists(self.save_file):
            open(self.save_file, "w").close()

    def save_content(self, content: str):
        with open(self.save_file, "w") as file:
            file.write(content)
            file.close()

    def load_content(self) -> dict:
        try:
            with open(self.save_file, "r+") as file:
                content = "".join(file.readlines())
                dictionary = json.loads(content)
                file.close()
        except JSONDecodeError:
            dictionary = {}
        return dictionary

    def save_user(self, user):
        dictionary = self.load_content()
        user_content = {
            "hash_key": user.get_password_hash(),
            "stocks": user.get_stocks(),
            "balance": user.get_balance_cents()
        }
        dictionary[user.get_user_name()] = user_content
        self.save_content(json.dumps(dictionary))

    def load_user(self, user_name: str):
        dictionary = self.load_content()
        if user_name in dictionary:
            return dictionary[user_name]
        return {}


class Portfolio:

    def __init__(self, balance: int, stocks: dict = None):
        if stocks is None:
            stocks = "{}"
        self.balance = balance
        self.stocks = stocks  # Mapping of [StockName: str, StockAmount: int]

    def sell_stock(self, stock_name: str, stock_price: int, amount: int):
        self.balance += (stock_price * amount) // 100
        amount = self.get_holding(stock_name) - amount
        self.stocks[stock_name] = amount

    def buy_stock(self, stock_name: str, stock_price: int, amount: int):
        self.balance -= (stock_price * amount) // 100
        amount += self.get_holding(stock_name)
        self.stocks[stock_name] = amount

    def get_holding(self, stock_name: str):
        if stock_name in self.stocks:
            return self.stocks[stock_name]
        return 0


def exists_user(user_name: str, database: Database):
    content = database.load_content()
    return user_name in content


def create_user(user_name: str, password: str, balance: int, database: Database):
    hash_key = generate_hash_key(password)
    user = User(user_name, hash_key, {}, balance, database)
    database.save_user(user)
    log_message(f"Created user {user} with a balance of {user.get_balance_string()}.")


def load_user(user_name: str, password: str, database: Database):
    user_content = database.load_user(user_name)
    if user_content is not {}:
        hash_key = user_content["hash_key"]
        if hash_key == generate_hash_key(password):
            stocks = user_content["stocks"]
            balance = user_content["balance"]
            return User(user_name, hash_key, stocks, balance, database)
    return None


class User:
    user_name: str
    hash_key: str
    portfolio: Portfolio

    def __init__(self, user_name: str, hash_key: str, stocks: dict[str, int], balance: int, database: Database):
        if stocks is None:
            stocks = {}
        self.user_name = user_name
        self.hash_key = hash_key
        self.portfolio = Portfolio(balance, stocks)
        self.database = database

    def check_password(self, password: str) -> bool:
        return generate_hash_key(password) == self.hash_key

    def change_password(self, password: str):
        self.hash_key = generate_hash_key(password)

    def get_user_name(self):
        return self.user_name

    def get_password_hash(self):
        return self.hash_key

    def get_portfolio(self):
        return self.portfolio

    def get_stocks(self):
        return self.portfolio.stocks

    def get_balance_cents(self) -> int:
        return self.portfolio.balance

    def get_balance_euros(self) -> float:
        return self.portfolio.balance / 100

    def get_balance_string(self) -> str:
        return "{:.2f}€".format(round(self.get_balance_cents() / 100, 2))

    def save_user(self) -> None:
        self.database.save_user(self)
