from typing import List


def get_training_data(ticker_data: List[float], input_period: int, scale_values: bool = True):
    x = []
    y = []
    scaling_factor = max(ticker_data)
    if scale_values:
        ticker_data = [(element / scaling_factor) for element in
                       ticker_data]  # Normalize values for more efficient and accurate training

    for i in range(len(ticker_data)):
        if i < input_period:
            i = input_period
        training_data = []
        for time in range(input_period):
            training_data.append(ticker_data[i - input_period - time])
        x.append(training_data)
        y.append(ticker_data[i])

    return x, y, scaling_factor
