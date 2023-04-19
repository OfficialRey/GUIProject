import random
from typing import List

from keras import Sequential
from keras.layers import Dense, ReLU
from keras.losses import MeanSquaredError
from keras.optimizers import Adam

from data import get_training_data
from stock_data.stocks import Stonks
from util.util import download_stock_data


class Model:
    model: Sequential

    def __init__(self, stocks: Stonks, stock_name: str, days_input_period: int = 28, scale_values: bool = True):

        data = download_stock_data([stock_name], "max")
        print(data)

        self.scaling = 1  # Used to scale data from normalized
        self.create_model(days_input_period)
        prices = stocks.get_stock_prices(stock_name)
        x, y = get_training_data(prices, days_input_period)
        self.train_model(x, y)

    def create_model(self, days_input_period: int):
        self.model = Sequential([
            Dense(days_input_period),
            Dense(256, activation=ReLU()),
            Dense(256, activation=ReLU()),
            Dense(256, activation=ReLU()),
            Dense(1, activation=ReLU())
        ])

        self.model.compile(
            optimizer=Adam(
                learning_rate=0.01,
            ),
            loss="mse",
            metrics=[MeanSquaredError()],
        )

        return self.model

    def train_model(self, x, y):
        if self.model is not None:
            self.model.fit(x, y, epochs=20)

        print(x[0])

        for i in range(20):
            index = random.randint(0, len(x))
            print(f"Prediction: {self.model(x[index])} | Target: {y[index]}")
