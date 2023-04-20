from typing import List

import numpy
import pandas as pd
import pyqtgraph

from util.util import time_stamp_to_string


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


class CompareGraph:

    def __init__(self, x: List[List[numpy.datetime64]], y: List[List[float]]):
        self.graph = pyqtgraph.PlotWidget()
        self.x = x
        self.y = y

    def plot_graph(self):
        pass

    def show_graph(self, index: int):
        pass

    def hide_graph(self, index: int):
        pass
