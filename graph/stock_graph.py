import pyqtgraph


class StockGraph:

    def __init__(self, x, y):
        self.graph = pyqtgraph.PlotWidget()
        self.graph.setBackground(background='white')
        self.graph.plot(x, y)

    def get_widget(self):
        return self.graph
