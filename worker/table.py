from PyQt5.QtCore import QObject, pyqtSignal
from stock_data.stocks import Stock, Stonks


class StockTableItemWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(Stock)

    def __init__(self, stonks_inst: Stonks):
        super(StockTableItemWorker, self).__init__()
        self.stonks_inst = stonks_inst
    
    def run(self):
        for stock_name in self.stonks_inst.get_stock_names():
            stock = self.stonks_inst.get_stock(stock_name)
            self.progress.emit(stock)
        self.finished.emit()