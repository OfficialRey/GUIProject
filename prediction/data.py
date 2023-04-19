from typing import List


def get_training_data(ticker_data: List[float], input_period: int, scale_values: bool = True):
    x = []
    y = []
    maximum = max(ticker_data)
    if scale_values:
        for i in range(len(ticker_data)):
            ticker_data[i] /= maximum

    for i in range(len(ticker_data)):
        if i < input_period:
            i = input_period
        training_data = []
        for time in range(input_period):
            training_data.append(ticker_data[i - input_period - time])
        x.append(training_data)
        y.append(ticker_data[i])

    print(y)

    return x, y
