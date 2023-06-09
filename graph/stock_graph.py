from typing import List

import numpy
import pandas as pd
import pyqtgraph

from util.util import time_stamp_to_string, expand_time_stamps


def create_axis_ticks(time_stamps: List[numpy.datetime64]) -> dict:
    content = [time_stamp_to_string(time_stamps[0])]

    for i in range(1, len(time_stamps) - 1):
        stamp = pd.Timestamp(time_stamps[i])
        if stamp.day == 1 or (stamp.day == stamp.days_in_month // 2 and False):
            content.append(time_stamp_to_string(stamp))
        else:
            content.append("")

    content.append(time_stamp_to_string(time_stamps[-1]))
    content = dict(enumerate(content))
    return content


COLORS = ["red", "blue"]
COMPARE_COLORS = ["green", "blue", "cyan", "magenta", "yellow", "gray", "darkRed", "darkGreen", "darkBlue", "darkCyan",
                  "darkMagenta", "darkGray", "lightGray"]


class StockGraph:

    def __init__(self, x: List[numpy.datetime64], y: List[float]):
        self.graph = pyqtgraph.PlotWidget()
        self.graph.setBackground(background='white')
        axis = self.graph.getAxis('bottom')
        x_content = create_axis_ticks(x)
        axis.setTicks([x_content.items()])
        self.graph.plot(list(x_content.keys()), y)

    def get_widget(self):
        return self.graph


class StockPredictionGraph:

    def __init__(self, history_x: List[numpy.datetime64], history_y: List[float], prediction_y: List[float],
                 compare_x=None, compare_y=None):

        if compare_y is None:
            compare_y = []
        if compare_x is None:
            compare_x = []

        self.graph = pyqtgraph.PlotWidget()
        self.graph.setBackground(background='white')

        # Calculate prediction values
        ticks = list(history_x)
        prediction_x = []
        if len(prediction_y) > 0:
            prediction_x: List[numpy.datetime64] = expand_time_stamps(history_x, len(prediction_y))
            prediction_x = list(prediction_x)[-(len(prediction_y) + 1):]
            prediction_y.insert(0, history_y[-1])
            prediction_y = pd.Series(prediction_y, index=prediction_x)
            ticks.extend(prediction_x)

        axis = self.graph.getAxis('bottom')
        x_content = create_axis_ticks(ticks)
        axis.setTicks([x_content.items()])

        self.graph.plot(history_x, history_y, pen=pyqtgraph.mkPen('black'))
        if len(prediction_y) > 0:
            self.graph.plot(prediction_x, prediction_y, pen=pyqtgraph.mkPen('red'))
        for i in range(min(len(compare_x), len(COMPARE_COLORS))):
            self.graph.plot(compare_x[i], compare_y[i], pen=pyqtgraph.mkPen(COMPARE_COLORS[i]))

    def get_widget(self):
        return self.graph
