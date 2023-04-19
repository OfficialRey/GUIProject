import sys
import json

from graph.stock_graph import StockGraph
from stock_data.stocks import Stonks
from PyQt5 import uic, QtWidgets, QtGui
import hashlib

from stock_data.stock_page import StockPage


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self.current_user = ""

        super(MainWindow, self).__init__()
        uic.loadUi("main.ui", self)

        self.stocks = Stonks()
        self.page = StockPage(stock_names=self.stocks.get_stock_names(), page_contents=10)

        self.set_stock_details(self.stocks.get_stock_names()[0])

        with open("style.qss") as f:
            self.setStyleSheet(f.read().strip())

        with open("users.json") as f:
            self.user_list = json.load(f)

        self.set_user_tab_state(False)
        self.add_functions()
        self.add_stock_table()
        self.set_icons()

    def set_stock_details(self, stock_id):
        stock_name = self.findChild(QtWidgets.QLabel, "stockName")
        target_stock = self.stocks.get_stock(stock_id)
        stock_name.setText(f"{target_stock.get_long_name()} ({stock_id})")
        stock_price = self.findChild(QtWidgets.QLabel, "stockPrice")
        stock_price.setText(f"{target_stock.get_ask_price()} {target_stock.get_currency()}")
        stock_price_diff = self.findChild(QtWidgets.QLabel, "stockPriceDiff")
        stock_trend = target_stock.get_stock_trend(7)
        sign = "+" if stock_trend > 0 else ""
        stock_price_diff.setText(f"({sign}{'{:4.2f}'.format(stock_trend)}%)")

        # TODO: load further info like category and market capital and graph of last 6 months

    def add_stock_table(self):
        stock_table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        stock_names = self.page.get_page()
        for i in range(len(stock_names)):
            target_stock = self.stocks.get_stock(stock_names[i])
            stock_trend = target_stock.get_stock_trend(7)
            stock_graph = StockGraph(target_stock.get_time_stamps(), target_stock.get_prices())
            sign = "+" if stock_trend > 0 else ""
            icon = QtGui.QIcon("info_logo.png")
            info_widget = QtWidgets.QPushButton()
            info_widget.setIcon(icon)
            info_widget.clicked.connect(self.show_stock_info)
            stock_table.insertRow(stock_table.rowCount())

            vertical_header = stock_table.verticalHeader()
            vertical_header.setDefaultSectionSize(120)

            stock_table.setCellWidget(i, 0, info_widget)
            stock_table.setCellWidget(i, 1, QtWidgets.QLabel(f"{stock_names[i]}"))
            stock_table.setCellWidget(i, 2, QtWidgets.QLabel(f"{target_stock.get_long_name()}"))
            stock_table.setCellWidget(i, 3,
                                      QtWidgets.QLabel(f"{target_stock.get_ask_price()} {target_stock.get_currency()}"))
            stock_table.setCellWidget(i, 4, QtWidgets.QLabel(f"({sign}{'{:4.2f}'.format(stock_trend)}%)"))
            stock_table.setCellWidget(i, 5, stock_graph.get_widget())

    def show_stock_info(self):
        table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        row = table.currentRow()

        stock_id = table.cellWidget(row, 1).text()
        self.set_stock_details(stock_id)

        tab_widget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        tab_widget.setCurrentIndex(3)

    def add_functions(self):
        self.findChild(QtWidgets.QLineEdit, "stockNameSearch").textChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QSlider, "stockPriceFilter").valueChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QSlider, "stockPriceFilter2").valueChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QPushButton, "loginButton").clicked.connect(self.on_login_button)
        self.findChild(QtWidgets.QAction, "actionExit").triggered.connect(self.on_exit)
        self.findChild(QtWidgets.QPushButton, "logoutButton").clicked.connect(self.on_logout)
        self.findChild(QtWidgets.QPushButton, "confirmChangePassword").clicked.connect(self.change_password)
        self.findChild(QtWidgets.QCheckBox, "positiveTrendsCheck").stateChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QCheckBox, "negativeTrendsCheck").stateChanged.connect(self.on_search_changed)

    def on_exit(self):
        self.close()

    def change_password(self):
        current_pwd = self.findChild(QtWidgets.QLineEdit, "currentPassword")
        current_pwd_hash = hashlib.sha256()
        current_pwd_hash.update(current_pwd.text().encode("utf-8"))
        new_pwd = self.findChild(QtWidgets.QLineEdit, "newPassword")
        new_pwd_hash = hashlib.sha256()
        new_pwd_hash.update(new_pwd.text().encode("utf-8"))
        confirm_pwd = self.findChild(QtWidgets.QLineEdit, "confirmPassword")

        if self.user_list[self.current_user]["password"] == current_pwd_hash.hexdigest():
            if new_pwd.text() == confirm_pwd.text():
                self.user_list[self.current_user]["password"] = new_pwd_hash.hexdigest()
                self.save_user_data()
                # TODO: set normal border
                current_pwd.setText("")
                new_pwd.setText("")
                confirm_pwd.setText("")
            else:
                pass
                # red border
        else:
            pass
            # red border

    def on_login_button(self):
        username_input = self.findChild(QtWidgets.QLineEdit, "usernameLineEdit").text()
        password_input = self.findChild(QtWidgets.QLineEdit, "passwordLineEdit").text()
        password_input_hash = hashlib.sha256()
        password_input_hash.update(password_input.encode("utf-8"))

        for username in self.user_list.keys():
            if username == username_input:
                if self.user_list[username]["password"] == password_input_hash.hexdigest():
                    self.on_login(username)
                else:
                    self.findChild(QtWidgets.QLineEdit, "passwordLineEdit").setStyleSheet("border: 1px solid red; padding-top: 2px; \
                                                                                          padding-bottom: 2px; border-radius: 2px;")

    def on_login(self, username):
        balance = self.user_list[username]["balance"]
        self.findChild(QtWidgets.QLabel, "userInfoBalanceValue").setText("{:.2f}€".format(balance))
        self.findChild(QtWidgets.QLineEdit, "passwordLineEdit").setStyleSheet("")
        self.findChild(QtWidgets.QLabel, "welcomeLabel").setText("Hi, {}".format(username))
        self.set_login_tab_state(False)
        self.set_user_tab_state(True)
        self.findChild(QtWidgets.QTabWidget, "tabWidget").setCurrentIndex(1)
        self.current_user = username

    def on_logout(self):
        tabWidget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        tabWidget.setTabEnabled(0, True)
        tabWidget.setStyleSheet(tabWidget.styleSheet())
        balance = self.findChild(QtWidgets.QLabel, "userInfoBalanceValue")
        balance.setText("0.00€")
        self.findChild(QtWidgets.QLabel, "welcomeLabel").setText("")
        self.findChild(QtWidgets.QLineEdit, "usernameLineEdit").setText("")
        self.findChild(QtWidgets.QLineEdit, "passwordLineEdit").setText("")
        self.set_user_tab_state(False)
        self.set_login_tab_state(True)
        tabWidget.setCurrentIndex(0)

    def set_login_tab_state(self, state):
        tabWidget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        tabWidget.setTabEnabled(0, state)
        tabWidget.setStyleSheet(tabWidget.styleSheet())

    def set_user_tab_state(self, state):
        tabWidget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        tabWidget.setTabEnabled(1, state)
        tabWidget.setStyleSheet(tabWidget.styleSheet())

    def on_search_changed(self):
        search = self.findChild(QtWidgets.QLineEdit, "stockNameSearch").text()
        value_lower = self.findChild(QtWidgets.QSlider, "stockPriceFilter").value()
        value_upper = self.findChild(QtWidgets.QSlider, "stockPriceFilter2").value()
        positive_check = self.findChild(QtWidgets.QCheckBox, "positiveTrendsCheck").isChecked()
        negative_check = self.findChild(QtWidgets.QCheckBox, "negativeTrendsCheck").isChecked()

        if value_lower > value_upper:
            slider = self.findChild(QtWidgets.QSlider, "stockPriceFilter2")
            slider.setValue(value_lower + 1)
            value_upper += 1
        if value_upper < value_lower:
            slider = self.findChild(QtWidgets.QSlider, "stockPriceFilter")
            slider.setValue(value_upper - 1)
            value_lower -= 1

        # TODO: new search algorithm for stock data pages

    def set_icons(self):
        self.setWindowIcon(QtGui.QIcon("logo.png"))
        self.findChild(QtWidgets.QPushButton, "logoutButton").setIcon(QtGui.QIcon("logout.png"))

    def save_user_data(self):
        with open("users.json", "w") as f:
            json.dump(self.user_list, f)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
