import math
from typing import List
from enum import Enum

import pandas as pd
import requests
import yfinance

TICKER_LIST_URL = "https://www.cboe.com/us/equities/market_statistics/listed_symbols/csv"
TARGET_INDEX = "Close"


class StockInfoKey(Enum):
    ASK_SIZE = "askSize"
    BID_SIZE = "bidSize"
    ASK_PRICE = "ask"
    BID_PRICE = "bid"
    CURRENCY = "currency"
    TRADEABLE = "tradeable"
    SHORT_NAME = "shortName"
    LONG_NAME = "longName"


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


def download_stock_names():
    stock_names = []
    response = requests.get(TICKER_LIST_URL)
    if response.ok:
        content = response.text.split("\n")[1:]
        for line in content:
            stock_names.append(line.split(",")[0])
        return stock_names
    else:
        raise ConnectionError("Cannot get ticker file")


def download_stock_data(stock_names: List[str], period: Period = Period.SIX_MONTHS):
    return yfinance.download(stock_names, period=period.value)


def get_date_period(start_date: pd.Timestamp, end_date: pd.Timestamp):
    dates = []
    current_date = start_date
    while current_date != end_date:
        dates.append(current_date)
        current_date = get_next_day(current_date)
    return dates


def get_next_day(date: pd.Timestamp):
    day = date.day
    month = date.month
    year = date.year
    day += 1
    if day > date.days_in_month:
        day = 1
        month += 1
        if month > 12:
            month = 1
            year += 1
    return pd.Timestamp(second=date.second, minute=date.minute, hour=date.hour, day=day, month=month, year=year)


def fill_data(data: pd.DataFrame):
    data_frame = pd.DataFrame()
    columns = data.columns.get_level_values(1)

    start_date = pd.Timestamp(data.index.values[0])
    end_date = pd.Timestamp(data.index.values[-1])

    time_stamps = get_date_period(start_date, end_date)
    data_frame.index = time_stamps

    for stock_name in columns:
        stock_data = []
        relevant_data = data[(TARGET_INDEX, stock_name)]
        last_value = math.nan
        for time_stamp in time_stamps:
            if time_stamp.to_numpy() in relevant_data.index.values:
                last_value = relevant_data.loc[time_stamp]
            stock_data.append(last_value)

        # Add column
        data_frame[stock_name] = stock_data
    return data_frame


def create_stock_infos(stock_names: List[str]):
    tickers = yfinance.Tickers(" ".join(stock_names))
    stock_infos = {}
    # Searching through a dict takes forever
    for stock_name in stock_names:
        info = tickers.tickers[stock_name].info
        if info:
            stock_infos[stock_name] = StockInfo(tickers.tickers[stock_name].info)
    return stock_infos


def get_value(key: str, info: dict):
    if key in info:
        return info[key]
    else:
        return 0


class StockInfo:
    bid_price: int
    bid_size: int
    ask_price: int
    ask_size: int
    currency: str
    tradeable: bool
    short_name: str
    long_name: str

    def __init__(self, ticker_info: dict):
        self.create_info(ticker_info)

    def create_info(self, ticker_info: dict):
        self.bid_price = get_value(StockInfoKey.BID_PRICE.value, ticker_info)
        self.bid_size = get_value(StockInfoKey.BID_SIZE.value, ticker_info)
        self.ask_price = get_value(StockInfoKey.ASK_PRICE.value, ticker_info)
        self.ask_size = get_value(StockInfoKey.ASK_SIZE.value, ticker_info)
        self.currency = get_value(StockInfoKey.CURRENCY.value, ticker_info)
        self.tradeable = get_value(StockInfoKey.TRADEABLE.value, ticker_info)
        self.short_name = get_value(StockInfoKey.SHORT_NAME.value, ticker_info)
        self.long_name = get_value(StockInfoKey.LONG_NAME.value, ticker_info)


class Stonks:

    def __init__(self):
        self.stock_names = download_stock_names()
        self.stock_prices = download_stock_data(self.stock_names)
        self.stock_info = create_stock_infos(self.stock_names)
        self.price_data = fill_data(self.stock_prices)

    def get_stock_prices(self, stock_name: str) -> List[float]:
        if stock_name in self.stock_prices:
            return self.stock_prices[stock_name]
        raise KeyError(f"Stock with symbol {stock_name} does not exist")

    def get_stock_info(self, stock_name: str) -> StockInfo:
        if stock_name in self.stock_info:
            return self.stock_info[stock_name]
        else:
            raise KeyError(f"Stock information for symbol {stock_name} does not exist")

    def get_stock_names(self) -> List[str]:
        return self.stock_names
