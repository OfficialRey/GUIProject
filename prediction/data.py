from typing import List


def get_training_data(ticker_data: List[float], input_period: int, scale_values: bool = True):
    print("training_data ticker data", ticker_data)
    print("training_data period", input_period)
    print("training_data do scale", scale_values)
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

    # TODO: WHY THE FUCK IS THIS A LIST WITH ONLY NAN VALUES
    print("training_data x", x[0])
    print("training_data y", y)

    return x, y, scaling_factor
