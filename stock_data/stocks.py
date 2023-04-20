import time
from typing import List
from enum import Enum

import pandas as pd
import yfinance
from requests import HTTPError

from util.util import get_value, download_stock_names, download_stock_data, fill_data, \
    calculate_stock_trend

TICKER_LIST_URL = "https://www.cboe.com/us/equities/market_statistics/listed_symbols/csv"
TARGET_INDEX = "Close"

MONTHS_IN_YEAR = 12
PRICE = "Price"


class TimeInterval(Enum):
    DAY = 1
    WEEK = 7
    MONTH = 30
    YEAR = 365


class StockInfoKey:
    ASK_SIZE = "askSize"
    BID_SIZE = "bidSize"
    ASK_PRICE = "ask"
    BID_PRICE = "bid"
    CURRENCY = "currency"
    TRADEABLE = "tradeable"
    SHORT_NAME = "shortName"
    LONG_NAME = "longName"


DEFAULT_STOCK_INFO = {
    StockInfoKey.BID_PRICE: "No information",
    StockInfoKey.BID_SIZE: "No information",
    StockInfoKey.ASK_PRICE: "No information",
    StockInfoKey.ASK_SIZE: "No information",
    StockInfoKey.CURRENCY: "-",
    StockInfoKey.TRADEABLE: "No information",
    StockInfoKey.SHORT_NAME: "No information",
    StockInfoKey.LONG_NAME: "No information"
}


class Period(Enum):
    ONE_DAY = "1d"
    ONE_WEEK = "7d"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    TEN_YEARS = "10y"


class Stock:

    def __init__(self, data_frame: pd.DataFrame, stock_name: str):
        self.stock_name = stock_name
        self.data: pd.DataFrame = data_frame

        trend_data = fill_data(self.data, stock_name)

        self.prices = trend_data[PRICE]
        self.time_stamps = trend_data.index.values
        self.meta_data = self.create_meta_data()

    def create_meta_data(self, max_attempts: int = 5):
        for i in range(max_attempts):
            try:
                ticker_info = yfinance.Ticker(self.stock_name).info
                return {StockInfoKey.BID_PRICE: get_value(StockInfoKey.BID_PRICE, ticker_info),
                        StockInfoKey.BID_SIZE: get_value(StockInfoKey.BID_SIZE, ticker_info),
                        StockInfoKey.ASK_PRICE: get_value(StockInfoKey.ASK_PRICE, ticker_info),
                        StockInfoKey.ASK_SIZE: get_value(StockInfoKey.ASK_SIZE, ticker_info),
                        StockInfoKey.CURRENCY: get_value(StockInfoKey.CURRENCY, ticker_info),
                        StockInfoKey.TRADEABLE: get_value(StockInfoKey.TRADEABLE, ticker_info),
                        StockInfoKey.SHORT_NAME: get_value(StockInfoKey.SHORT_NAME, ticker_info),
                        StockInfoKey.LONG_NAME: get_value(StockInfoKey.LONG_NAME, ticker_info)}
            except HTTPError:
                time.sleep(0.1)

        return DEFAULT_STOCK_INFO

    def get_stock_trend(self, period: int):
        return calculate_stock_trend(self.prices, period)

    def get_bid_price(self):
        return self.meta_data[StockInfoKey.BID_PRICE]

    def get_bid_size(self):
        return self.meta_data[StockInfoKey.BID_SIZE]

    def get_ask_price(self):
        return self.meta_data[StockInfoKey.ASK_PRICE]

    def get_ask_size(self):
        return self.meta_data[StockInfoKey.ASK_SIZE]

    def get_currency(self):
        return self.meta_data[StockInfoKey.CURRENCY]

    def is_tradeable(self):
        return self.meta_data[StockInfoKey.TRADEABLE]

    def get_short_name(self):
        return self.meta_data[StockInfoKey.SHORT_NAME]

    def get_long_name(self):
        return self.meta_data[StockInfoKey.LONG_NAME]

    def get_prices(self):
        return self.prices

    def get_time_stamps(self) -> List[pd.Timestamp]:
        return self.time_stamps


class Stonks:

    def __init__(self, stock_names=None):
        self.stock_names = download_stock_names(TICKER_LIST_URL) if stock_names is None else stock_names
        self.stock_data = download_stock_data(self.stock_names, Period.SIX_MONTHS.value)
        self.stocks: dict = {}

    def get_stock(self, stock_name: str) -> Stock:
        if stock_name not in self.stocks:
            self.stocks[stock_name] = Stock(self.stock_data, stock_name)
        return self.stocks[stock_name]

    def get_stocks(self, stock_names: List[str]):
        stocks = []
        for stock_name in stock_names:
            stocks.append(self.get_stock(stock_name))
        return stocks

    def get_stock_names(self) -> List[str]:
        return self.stock_names
