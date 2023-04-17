import sys
import json
from PyQt5 import uic, QtWidgets
import stock_list_item
from stock_data.stocks import Stonks


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("main.ui", self)

        self.stocks = Stonks()

        with open("users.json") as f:
            self.user_list = json.load(f)

        self.add_functions()
        self.add_stock_list()

    def add_stock_list(self):
        stock_list = self.findChild(QtWidgets.QListWidget, "stockDetailList")
        stock_names = self.stocks.get_stock_names()
        for stock_name in stock_names:
            stock_info = self.stocks.get_stock_info(stock_name)
            item = QtWidgets.QListWidgetItem()
            stock_list.addItem(item)

            custom_content = stock_list_item.StockListWidgetItem(f"{stock_info.long_name} ({stock_name})",
                                                                 stock_info.ask_price, stock_info.currency)
            item.setSizeHint(custom_content.minimumSizeHint())
            stock_list.setItemWidget(item, custom_content)

    def add_functions(self):
        self.findChild(QtWidgets.QLineEdit, "stockNameSearch").textChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QSlider, "stockPriceFilter").valueChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QSlider, "stockPriceFilter2").valueChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QPushButton, "loginButton").clicked.connect(self.on_login)

    def on_login(self):
        username_input = self.findChild(QtWidgets.QLineEdit, "usernameLineEdit").text()
        password_input = self.findChild(QtWidgets.QLineEdit, "passwordLineEdit").text()

        for username in self.user_list.keys():
            if username == username_input:
                if self.user_list[username]["password"] == password_input:
                    balance = self.user_list[username]["balance"]
                    self.findChild(QtWidgets.QLabel, "userInfoBalanceValue").setText("{:.2f}€".format(balance))

    def on_search_changed(self):
        search = self.findChild(QtWidgets.QLineEdit, "stockNameSearch").text()
        value_lower = self.findChild(QtWidgets.QSlider, "stockPriceFilter").value()
        value_upper = self.findChild(QtWidgets.QSlider, "stockPriceFilter2").value()
        stock_list = self.findChild(QtWidgets.QListWidget, "stockDetailList")

        if value_lower > value_upper:
            slider = self.findChild(QtWidgets.QSlider, "stockPriceFilter2")
            slider.setValue(value_lower + 1)
            value_upper += 1
        if value_upper < value_lower:
            slider = self.findChild(QtWidgets.QSlider, "stockPriceFilter")
            slider.setValue(value_upper - 1)
            value_lower -= 1

        for i in range(stock_list.count()):
            item = stock_list.item(i)
            if search.lower() not in stock_list.itemWidget(item).stock_name_label.text().lower() or \
                    value_lower > float(stock_list.itemWidget(item).stock_price_label.text()[:-1]) or \
                    value_upper < float(stock_list.itemWidget(item).stock_price_label.text()[:-1]):
                stock_list.item(i).setHidden(True)
            else:
                stock_list.item(i).setHidden(False)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
