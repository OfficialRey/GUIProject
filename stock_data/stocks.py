from typing import List
from enum import Enum

import numpy
import pandas as pd
import yfinance

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
    CURRENT_PRICE = "curPrice"
    ASK_SIZE = "askSize"
    BID_SIZE = "bidSize"
    ASK_PRICE = "ask"
    BID_PRICE = "bid"
    CURRENCY = "currency"
    TRADEABLE = "tradeable"
    SHORT_NAME = "shortName"
    LONG_NAME = "longName"
    INDUSTRY = "industry"
    SECTOR = "sector"
    WEBSITE = "website"
    COUNTRY = "country"
    CITY = "city"
    DIVIDEND_RATE = "dividendRate"
    DIVIDEND_YIELD = "dividendYield"
    VOLUME = "volume"


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

    def create_meta_data(self):
        ticker_info = yfinance.Ticker(self.stock_name).info
        if ticker_info[StockInfoKey.ASK_PRICE] == 0:
            ticker_info[StockInfoKey.ASK_PRICE] = self.prices[-1]
        return {
            StockInfoKey.BID_PRICE: get_value(StockInfoKey.BID_PRICE, ticker_info),
            StockInfoKey.BID_SIZE: get_value(StockInfoKey.BID_SIZE, ticker_info),
            StockInfoKey.ASK_PRICE: get_value(StockInfoKey.ASK_PRICE, ticker_info),
            StockInfoKey.ASK_SIZE: get_value(StockInfoKey.ASK_SIZE, ticker_info),
            StockInfoKey.CURRENCY: get_value(StockInfoKey.CURRENCY, ticker_info),
            StockInfoKey.TRADEABLE: get_value(StockInfoKey.TRADEABLE, ticker_info),
            StockInfoKey.SHORT_NAME: get_value(StockInfoKey.SHORT_NAME, ticker_info),
            StockInfoKey.LONG_NAME: get_value(StockInfoKey.LONG_NAME, ticker_info),
            StockInfoKey.WEBSITE: get_value(StockInfoKey.WEBSITE, ticker_info),
            StockInfoKey.COUNTRY: get_value(StockInfoKey.COUNTRY, ticker_info),
            StockInfoKey.CITY: get_value(StockInfoKey.CITY, ticker_info),
            StockInfoKey.SECTOR: get_value(StockInfoKey.SECTOR, ticker_info),
            StockInfoKey.INDUSTRY: get_value(StockInfoKey.INDUSTRY, ticker_info),
            StockInfoKey.VOLUME: get_value(StockInfoKey.VOLUME, ticker_info),
            StockInfoKey.DIVIDEND_RATE: get_value(StockInfoKey.DIVIDEND_RATE, ticker_info),
            StockInfoKey.DIVIDEND_YIELD: get_value(StockInfoKey.DIVIDEND_YIELD, ticker_info)
        }

    def get_name(self):
        return self.stock_name

    def get_stock_trend(self, period: int):
        return calculate_stock_trend(self.prices, period)

    def get_bid_price(self):
        return self.meta_data[StockInfoKey.BID_PRICE]

    def get_bid_size(self):
        return self.meta_data[StockInfoKey.BID_SIZE]

    def get_ask_price(self):
        return self.meta_data[StockInfoKey.ASK_PRICE]

    def get_ask_price_cents(self):
        return self.get_ask_price() * 100

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

    def get_dividend_rate(self):
        return self.meta_data[StockInfoKey.DIVIDEND_RATE]

    def get_dividend_yield(self):
        return self.meta_data[StockInfoKey.DIVIDEND_YIELD]

    def get_country(self):
        return self.meta_data[StockInfoKey.COUNTRY]

    def get_city(self):
        return self.meta_data[StockInfoKey.CITY]

    def get_volume(self):
        return self.meta_data[StockInfoKey.VOLUME]

    def get_website(self):
        return self.meta_data[StockInfoKey.WEBSITE]

    def get_sector(self):
        return self.meta_data[StockInfoKey.SECTOR]

    def get_industry(self):
        return self.meta_data[StockInfoKey.INDUSTRY]

    def get_prices(self, period: int = -1):
        if period == -1:
            return self.prices
        return self.prices[-period:]

    def get_time_stamps(self, period: int = -1) -> List[numpy.datetime64]:
        if period == -1:
            return self.time_stamps
        return self.time_stamps[-period:]


class Stonks:

    def __init__(self, stock_names=None):
        self.stock_names = download_stock_names(TICKER_LIST_URL) if stock_names is None else stock_names
        self.stock_data = download_stock_data(self.stock_names, Period.TEN_YEARS.value)
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

    def fetch(self):
        for stock_name in self.stock_names:
            _ = self.get_stock(stock_name)
