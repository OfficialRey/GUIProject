import math
import random
from typing import List, Tuple

from util.util import fix_results


def remove_nan(ticker_data: List[float]) -> List[float]:
    new_data = []
    add = False
    for value in ticker_data:
        if value is not math.nan:
            add = True
        if add:
            new_data.append(value)
    return new_data


def get_training_data(ticker_data: List[float], input_period: int, scale_values: bool = True):
    ticker_data = remove_nan(ticker_data)
    x = []
    y = []
    scaling_factor = max(ticker_data)
    if scale_values:
        noise = (random.random() * 0.4 + 0.8)  # We add a tiny bit of noise to counter patterns in the predictions
        ticker_data = [((element * noise) / scaling_factor) for element in
                       ticker_data]  # Normalize values for more efficient and accurate training
        ticker_data = fix_results(ticker_data)

    for i in range(len(ticker_data)):
        if i < input_period:
            i = input_period
        training_data = []
        for time in range(input_period):
            training_data.append(ticker_data[i - input_period - time])
        x.append(training_data)
        y.append(ticker_data[i])

    return x, y, scaling_factor
