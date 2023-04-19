import random
from typing import List

import numpy as np
from keras import Sequential
from keras.layers import Dense, ReLU, LeakyReLU
from keras.losses import MeanSquaredError
from keras.optimizers import Adam

from data import get_training_data
from stock_data.stocks import Stock, Stonks


class StockPrediction:
    model: Sequential

    def __init__(self, stock: Stock, days_input_period: int = 28, scale_values: bool = True):
        self.period = days_input_period
        self.x, self.y, self.scaling_factor = get_training_data(stock.get_prices(), self.period, scale_values)
        self._create_model()
        self._train_model()

    def _create_model(self):
        # Avoiding ReLU to counter the "Dying ReLU" problem
        self.model = Sequential([
            Dense(self.period),
            Dense(256, activation='tanh'),
            Dense(256, activation=LeakyReLU()),
            Dense(256, activation='tanh'),
            Dense(1, activation=ReLU())
        ])

        self.model.compile(
            optimizer=Adam(
                learning_rate=0.0001,  # Low learning rate to counter "Dying ReLU" problem
            ),
            loss="mse",
            metrics=[MeanSquaredError()],
        )

        return self.model

    def _train_model(self):
        if self.model is not None:
            self.model.fit(self.x, self.y, epochs=20, verbose=1)

    def predict_future_stock_prices(self, period: int = 28):
        results = []
        current_period = self.x[-1]  # Get last period

        for i in range(period):
            # Use own prediction for next period
            result = self._predict(current_period)
            results.append(result)
            current_period.pop(0)
            current_period.append(result)
        return [element * self.scaling_factor for element in results]

    def _predict(self, x: List[float]):
        return self.model(np.array([x])).numpy()[0][0]


if __name__ == '__main__':
    stonks = Stonks()
    model = StockPrediction(stonks.get_stock(stonks.get_stock_names()[0]), days_input_period=28)
    predictions = model.predict_future_stock_prices()
    print(model.predict_future_stock_prices())
