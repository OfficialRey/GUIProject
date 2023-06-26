from typing import List, Union

from threading import Thread

import numpy as np
from keras import Sequential
from keras.layers import Dense
from keras.optimizers import Adam

from prediction.data import get_training_data
from util.util import post_process_results


class StockPrediction:
    model: Sequential = None

    def __init__(self, stocks: Union[object, List], days_input_period: int = 28, scale_values: bool = True,
                 threading: bool = True, verbose: int = 0):
        if not isinstance(stocks, list):
            stocks = [stocks]
        self.period = days_input_period
        self.cache = []
        self.x = []
        self.y = []
        self.ready = False
        if threading:
            self.thread = Thread(target=self._create_model, args=(stocks, scale_values))
            self.thread.start()
        else:
            self._create_model(stocks, scale_values, verbose)

    def _create_model(self, stocks: List, scale_values: bool = True, verbose: int = 0):
        if self.model is None:
            self.x = []
            self.y = []
            for stock in stocks:
                x, y, self.scaling_factor = get_training_data(stock.get_prices(), self.period, scale_values)
                self.x.extend(x)
                self.y.extend(y)
            self._create_network()
            self._train_model(verbose=verbose)

    def _create_network(self):
        # Avoiding ReLU to counter the "Dying ReLU" problem
        # Very big network to deny pattern creation
        self.model = Sequential([
            Dense(self.period),
            Dense(128, activation='tanh'),
            #Dense(512, activation='tanh'),
            #Dense(256, activation='tanh'),
            #Dense(64, activation='tanh'),
            #Dense(32, activation='tanh'),
            #Dense(16, activation='tanh'),
            Dense(1, activation='relu')  # Stock prices cannot be negative
        ])

        self.model.compile(
            optimizer=Adam(
                learning_rate=0.001,  # Low learning rate to counter "Dying ReLU" problem
            ),
            loss="mse",
            metrics=["mean_squared_error"],
        )

        return self.model

    def _train_model(self, x: List[List[float]] = None, y: List[float] = None, verbose: int = 0):
        if x is None or y is None:
            x = self.x
            y = self.y

        if self.model is not None:
            # Only short training time to deny patterns and allow creativity and freedom for the network
            self.model.fit(x, y, epochs=10, verbose=verbose)

    def _cache_results(self, results: List[float]):
        if len(results) < len(self.cache):
            return
        target_len = len(results) - len(self.cache)
        self.cache.extend(results[-target_len:])

    def predict_future_stock_prices(self, period: int = 28):
        if len(self.cache) >= period:
            return self.cache[:period]

        if self.model is not None:
            results = []
            current_period = self.x[-1]  # Get last period

            for i in range(period):
                # Use own prediction for next period
                result = self._predict(current_period)
                results.append(result)
                current_period.pop(0)
                current_period.append(result)
            results = [element * self.scaling_factor for element in results]
            results = post_process_results(results)

            # Replace results by cache content
            i = 0
            while i < len(results) and i < len(self.cache):
                results[i] = self.cache[i]
                i += 1

            self._cache_results(results)
            return results
        return []

    def _predict(self, x: List[float]):
        if self.model is not None:
            return self.model(np.array([x])).numpy()[0][0]
        return []

    def is_ready(self):
        return self.ready
