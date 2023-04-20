from PyQt5.QtCore import QObject, pyqtSignal


class StockTablePageWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, main_window, direction: bool):
        super(StockTablePageWorker, self).__init__()
        self.main_window = main_window
        self.direction = direction

    def run(self):
        if self.direction:
            self.main_window.pages.next_page()
        else:
            self.main_window.pages.previous_page()
        self.finished.emit()
