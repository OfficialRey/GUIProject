from typing import List

import pandas as pd
import pyqtgraph

from util.util import time_stamp_to_string


class StockGraph:

    def __init__(self, x: List[pd.Timestamp], y: List[float]):
        self.graph = pyqtgraph.PlotWidget()
        self.graph.setBackground(background='white')
        x_content = [time_stamp_to_string(pd.Timestamp(x[i])) for i in range(len(x))]
        x_content = dict(enumerate(x_content))
        axis = self.graph.getAxis('bottom')
        axis.setTicks([x_content.items()])
        self.graph.plot(list(x_content.keys()), y)

    def get_widget(self):
        return self.graph
