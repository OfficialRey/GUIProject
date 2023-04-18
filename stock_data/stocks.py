import math
import time
from typing import List
from enum import Enum

import pandas as pd
import requests
import yfinance
from requests import HTTPError

TICKER_LIST_URL = "https://www.cboe.com/us/equities/market_statistics/listed_symbols/csv"
TARGET_INDEX = "Close"

MONTHS_IN_YEAR = 12
PRICE = "Price"


class TimeInterval(Enum):
    DAY = 1
    WEEK = 7
    MONTH = 30
    YEAR = 365


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
    ONE_WEEK = "7d"
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


def add_time_stamp(date: pd.Timestamp, day: int = 0, month: int = 0, year: int = 0):
    # Approximation of target date
    # Not perfect but close enough to fulfill the use case
    current_day = date.day
    current_month = date.month
    current_year = date.year

    current_day += day
    while current_day > date.days_in_month:
        current_day -= date.days_in_month
        current_month += 1

    current_month += month
    while current_month > MONTHS_IN_YEAR:
        current_month -= MONTHS_IN_YEAR
        current_year += 1

    current_year += year

    return pd.Timestamp(second=date.second, minute=date.minute, hour=date.hour, day=current_day, month=current_month,
                        year=current_year)


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


def fill_data(data: pd.DataFrame, stock_name: str):
    data_frame = pd.DataFrame()

    start_date = pd.Timestamp(data.index.values[0])
    end_date = pd.Timestamp(data.index.values[-1])

    time_stamps = get_date_period(start_date, end_date)
    data_frame.index = time_stamps

    stock_data = []
    relevant_data = data[(TARGET_INDEX, stock_name)]
    last_value = math.nan
    for time_stamp in time_stamps:
        if time_stamp.to_numpy() in relevant_data.index.values:
            last_value = relevant_data.loc[time_stamp]
        stock_data.append(last_value)

    # Add column
    data_frame[PRICE] = stock_data
    return data_frame


def calculate_stock_trend(stock_prices: List[float], period: Period = Period.ONE_MONTH) -> float:
    current_price = stock_prices[-1]
    old_price = stock_prices[0]
    days_to_remove = 0
    if period == Period.ONE_DAY:
        days_to_remove = TimeInterval.DAY.value
    elif period == Period.ONE_WEEK:
        days_to_remove = TimeInterval.WEEK.value
    elif period == Period.ONE_MONTH:
        days_to_remove = TimeInterval.MONTH.value
    elif period == Period.THREE_MONTHS:
        days_to_remove = TimeInterval.MONTH.value * 3
    elif period == Period.SIX_MONTHS:
        days_to_remove = TimeInterval.MONTH.value * 6
    elif period == Period.ONE_YEAR:
        days_to_remove = TimeInterval.YEAR.value
    elif period == Period.TWO_YEARS:
        days_to_remove = TimeInterval.YEAR.value * 2
    elif period == Period.FIVE_YEARS:
        days_to_remove = TimeInterval.YEAR.value * 5
    elif period == Period.TEN_YEARS:
        days_to_remove = TimeInterval.YEAR.value * 10

    if len(stock_prices) > days_to_remove:
        old_price = stock_prices[-days_to_remove]
    trend = ((current_price / old_price) - 1) * 100
    return trend


def create_stock_infos(stock_names: List[str]):
    tickers = yfinance.Tickers(" ".join(stock_names))
    stock_infos = {}
    for stock_name in stock_names:
        info = tickers.tickers[stock_name].info
        if info:
            stock_infos[stock_name] = StockInfo(info)
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

    def __init__(self, stock_names=None):
        self.stock_names = download_stock_names() if stock_names is None else stock_names
        self.stock_prices = download_stock_data(self.stock_names)
        self.stock_info = {}
        self.price_data: dict = {}

    def create_stock_data(self, stock_name: str):
        if stock_name not in self.price_data:
            self.price_data[stock_name] = fill_data(self.stock_prices, stock_name)

    def get_stock_prices(self, stock_name: str) -> List[float]:
        self.create_stock_data(stock_name)
        return self.price_data[stock_name][PRICE].values

    def get_stock_trend(self, stock_name: str) -> float:
        return calculate_stock_trend(self.get_stock_prices(stock_name))

    def get_stock_info(self, stock_name: str) -> StockInfo:
        if stock_name not in self.stock_info.keys():
            done = False
            while not done:
                try:
                    info = StockInfo(yfinance.Ticker(stock_name).info)
                    self.stock_info[stock_name] = info
                    done = True
                except HTTPError:
                    time.sleep(0.5)
        return self.stock_info[stock_name]

    def get_stock_names(self) -> List[str]:
        return self.stock_names

    def get_stock_dates(self, stock_name: str) -> List[pd.Timestamp]:
        self.create_stock_data(stock_name)
        return self.price_data[stock_name].index.values
