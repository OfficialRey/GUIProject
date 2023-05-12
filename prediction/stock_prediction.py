from typing import List, Union

from threading import Thread

import numpy as np
import pandas as pd
from keras import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from keras.saving.saving_api import load_model

from prediction.data import get_training_data
from util.util import post_process_results, sanitize_file_name


class StockPrediction:
    model: Sequential = None

    def __init__(self, stocks: Union[object, List], days_input_period: int = 28, scale_values: bool = True,
                 threading: bool = True, save_file: str = None, verbose: int = 0):
        if save_file is None:
            save_file = f"prediction_model_{pd.Timestamp.today()}"
        if not isinstance(stocks, list):
            stocks = [stocks]
        self.period = days_input_period
        self.save_file = f"{sanitize_file_name(save_file)}.keras"
        self.x = []
        self.y = []
        self.ready = False
        if threading:
            self.thread = Thread(target=self._create_model, args=(stocks, scale_values))
            self.thread.start()
        else:
            self._create_model(stocks, scale_values, verbose)

    def _create_model(self, stocks: List, scale_values: bool = True, verbose: int = 0):
        self.load_model()
        if self.model is None:
            self.x = []
            self.y = []
            for stock in stocks:
                x, y, self.scaling_factor = get_training_data(stock.get_prices(), self.period, scale_values)
                self.x.extend(x)
                self.y.extend(y)
            self._create_network()
            self._train_model(verbose=verbose)
            self.save_model()

    def _create_network(self):
        # Avoiding ReLU to counter the "Dying ReLU" problem
        self.model = Sequential([
            Dense(self.period),
            Dense(128, activation='tanh'),
            Dense(64, activation='tanh'),
            Dense(32, activation='tanh'),
            Dense(16, activation='tanh'),
            Dense(8, activation='tanh'),
            Dense(1, activation='tanh')
        ])

        self.model.compile(
            optimizer=Adam(
                learning_rate=0.0001,  # Low learning rate to counter "Dying ReLU" problem
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
            # Heavily over-fit model to ensure non-negative entries and adapt to the single graph
            self.model.fit(x, y, epochs=100, verbose=verbose)

    def predict_future_stock_prices(self, period: int = 28):
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
            return post_process_results(results)
        return []

    def _predict(self, x: List[float]):
        if self.model is not None:
            return self.model(np.array([x])).numpy()[0][0]
        return []

    def save_model(self):
        if self.model is not None:
            self.model.save(self.save_file)
            self.ready = True

    def load_model(self):
        try:
            self.model = load_model(self.save_file)
            self.ready = True
        except IOError or FileExistsError or FileNotFoundError:
            pass

    def is_ready(self):
        return self.ready
