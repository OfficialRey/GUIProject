from typing import Tuple, List
from datetime import date
from enum import Enum

import requests
import yfinance as yf
import pandas as pd

import plotly.express as px

TICKER_LIST_URL = "https://www.cboe.com/us/equities/market_statistics/listed_symbols/csv"
TICKERS = []


class Period(Enum):
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    TEN_YEARS = "10y"


class StockInformation:

    def __init__(self, day: date, price: float):
        self.day = day
        self.price = price

    def __str__(self):
        return f"Date: {self.day} | Price: {self.price}"


def initialise():
    response = requests.get(TICKER_LIST_URL)
    if response.ok:
        global TICKERS
        TICKERS = []
        content = response.text.split("\n")[1:]
        for line in content:
            TICKERS.append(line.split(",")[0])
        update_stock_data()
    else:
        raise ConnectionError("Cannot get ticker file")


def update_stock_data():
    global TICKERS
    to_remove = []
    for stock_name in TICKERS:
        if not exists_stock_data(stock_name):
            to_remove.append(stock_name)

    for stock_name in to_remove:
        TICKERS.remove(stock_name)


def get_stock_names() -> List[str]:
    return TICKERS


def exists_stock_data(stock_name: str):
    ticker = yf.Ticker(stock_name)
    history, info = ticker.history(), ticker.info
    print(history)


def get_stock_data(stock_name: str, period: Period = Period.SIX_MONTHS) -> Tuple[pd.DataFrame, dict]:
    if not exists_stock_data(stock_name):
        raise ValueError(f"Stock data does not exist for stock '{stock_name}'")
    ticker = yf.Ticker(stock_name)
    return ticker.history(period=period), ticker.info


def get_stock_values(stock_history: pd.DataFrame):
    print(stock_history)
    stock_data = []
    for day, price in zip(stock_history.index, stock_history["Close"]):
        date_stamp = str(day).split(" ")[0]
        year, month, day = date_stamp.split("-")
        stock_data.append(StockInformation(day=date(year=int(year), month=int(month), day=int(day)), price=price))

    return stock_data


def plot_stock_data(stock_history: pd.DataFrame):
    fig = px.line(stock_history.iloc[::-1], y="Open")
    fig.show()


if __name__ == '__main__':
    exists_stock_data("I DONT EXIST")
