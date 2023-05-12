import math
from typing import List, Union

import numpy
import pandas as pd
import yfinance

MONTHS_IN_YEAR = 12

TARGET_INDEX = "Close"
PRICE = "Price"

ILLEGAL_CHARACTERS = ".:!?#&()[]{}/\\$§\"\'+-*@=|´`<> "


def download_stock_data(stock_names: List[str], period: str = "7d"):
    return yfinance.download(stock_names, period=period)


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


def download_stock_names(url: str):
    return ["AFX.DE", "AIXA.DE", "AT1.DE", "BC8.DE", "BFSA.DE", "BOSS.DE", "CBK.DE", "DHER.DE", "DUE.DE", "ECV.DE",
            "EVD.DE", "EVK.DE", "EVT.DE", "FNTN.DE", "FPE3.DE", "FRA.DE", "G1A.DE", "G24.DE", "GXI.DE", "HFG.DE",
            "HLE.DE", "JUN3.DE", "KBX.DE", "KGX.DE", "LEG.DE", "LHA.DE", "LXS.DE", "NDA.DE", "NEM.DE", "O2D.DE",
            "PSM.DE", "PUM.DE", "QH9.DE", "RAA.DE", "RHM.DE", "RRTL.DE", "SAX.DE", "SDF.DE", "SIX2.DE", "SOW.DE",
            "STM.DE", "TEG.DE", "TKA.DE", "TLX.DE", "TMV.DE", "UTDI.DE", "VBK.DE", "VTWR.DE", "WAF.DE", "WCH.DE"]
    '''stock_names = []
    response = requests.get(url)
    if response.ok:
        content = response.text.split("\n")[1:]
        for line in content:
            stock_names.append(line.split(",")[0])
        return stock_names
    else:
        raise ConnectionError("Cannot get ticker file")'''


def time_stamp_to_string(time_stamp: Union[pd.Timestamp, numpy.datetime64]) -> str:
    if isinstance(time_stamp, numpy.datetime64):
        time_stamp = pd.Timestamp(time_stamp)
    return f"{time_stamp.day}.{time_stamp.month}.{time_stamp.year}"


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


def calculate_stock_trend(stock_prices: List[float], period: int = 7) -> float:
    current_price = stock_prices[-1]
    old_price = stock_prices[0]

    if len(stock_prices) > period:
        old_price = stock_prices[-period]
    trend = ((current_price / old_price) - 1) * 100
    return trend


# def create_stock_infos(stock_names: List[str]):
#    tickers = yfinance.Tickers(" ".join(stock_names))
#    stock_infos = {}
#    for stock_name in stock_names:
#        info = tickers.tickers[stock_name].info
#        if info:
#            stock_infos[stock_name] = StockInfo(info)
#    return stock_infos


def get_value(key: str, info: dict):
    if key in info:
        return info[key]
    else:
        return 0


def post_process_results(results: List[float]):
    # Overwrite negative entries with previous non-negative values
    for i in range(1, len(results)):
        if results[i] < 0:
            results[i] = results[i - 1]
    return results


def sanitize_file_name(file_name: str):
    for character in ILLEGAL_CHARACTERS:
        file_name = file_name.replace(character, '')

    return file_name


def expand_time_stamps(time_stamps: List[numpy.datetime64], period: int):
    for i in range(period):
        numpy.append(time_stamps, add_time_stamp(pd.Timestamp(time_stamps[-1]), day=1).to_numpy())
    return time_stamps
