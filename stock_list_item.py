from PyQt5 import QtWidgets

class StockListWidgetItem(QtWidgets.QWidget):
    def __init__(self, stock_name, stock_price, parent=None):
        super(StockListWidgetItem, self).__init__(parent)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setSpacing(10)

        self.stock_name_label = QtWidgets.QLabel(stock_name)
        self.stock_name_label.setMinimumWidth(180)
        self.stock_price_label = QtWidgets.QLabel(stock_price + "€")
        self.stock_price_label.setMinimumWidth(50)

        self.layout.addWidget(self.stock_name_label)
        self.layout.addWidget(self.stock_price_label)
        self.layout.addItem(QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

        # TODO: add category (IT, Chemicals, Food, etc.) and price graph
        # add heading? if possible