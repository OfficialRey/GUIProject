import sys
import json

from graph.stock_graph import StockGraph
from logs.log import Logger
from stock_data.stocks import Stonks
from util.user import User
from PyQt5 import uic, QtWidgets, QtGui, QtCore
import hashlib
from workers import StockTablePageWorker

from stock_data.stock_page import StockPage


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("main.ui", self)

        self.stocks = Stonks()
        self.logs = Logger()
        self.pages = StockPage(stock_names=self.stocks.get_stock_names(), page_contents=10)

        self.set_stock_details(self.stocks.get_stock_names()[0])

        self.user_manager = User()

        with open("style.qss") as f:
            self.setStyleSheet(f.read().strip())

        self.set_user_tab_state(False)
        self.add_functions()
        self.update_stock_table()
        self.set_icons()

        self.logs.log_message("Program launched.")

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

    def update_stock_table(self):
        stock_table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        info_label: QtWidgets.QLabel = self.findChild(QtWidgets.QLabel, "stockTableLoadingIndicator")
        info_label.setText("")
        stock_table.setRowCount(0)
        stock_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        stock_names = self.pages.get_page()
        for i in range(len(stock_names)):
            target_stock = self.stocks.get_stock(stock_names[i])
            stock_trend = target_stock.get_stock_trend(7)
            stock_graph = StockGraph(target_stock.get_time_stamps(), target_stock.get_prices())
            sign = "+" if stock_trend > 0 else ""
            icon = QtGui.QIcon("assets/info_logo.png")
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
        self.findChild(QtWidgets.QCheckBox, "positiveTrendsCheck").stateChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QCheckBox, "negativeTrendsCheck").stateChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QPushButton, "loginButton").clicked.connect(self.on_login_button)
        self.findChild(QtWidgets.QAction, "actionExit").triggered.connect(self.on_exit)
        self.findChild(QtWidgets.QPushButton, "logoutButton").clicked.connect(self.on_logout)
        self.findChild(QtWidgets.QPushButton, "confirmChangePassword").clicked.connect(self.change_password)
        self.findChild(QtWidgets.QPushButton, "stockTablePrevPage").clicked.connect(
            lambda: self.create_stock_table_page_thread(False))
        self.findChild(QtWidgets.QPushButton, "stockTableNextPage").clicked.connect(
            lambda: self.create_stock_table_page_thread(True))

    def create_stock_table_page_thread(self, direction: bool):
        info_label: QtWidgets.QLabel = self.findChild(QtWidgets.QLabel, "stockTableLoadingIndicator")
        info_label.setText("Loading...")
        self.set_page_button_state(False)

        self.thread = QtCore.QThread()

        self.worker = StockTablePageWorker(self, direction)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.update_stock_table)
        self.worker.finished.connect(lambda: self.set_page_button_state(True))

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def set_page_button_state(self, state: bool):
        prev = self.findChild(QtWidgets.QPushButton, "stockTablePrevPage")
        next = self.findChild(QtWidgets.QPushButton, "stockTableNextPage")
        prev.setEnabled(state)
        next.setEnabled(state)

    def on_exit(self):
        self.close()

    def change_password(self):
        current_pwd = self.findChild(QtWidgets.QLineEdit, "currentPassword")
        new_pwd = self.findChild(QtWidgets.QLineEdit, "newPassword")
        confirm_pwd = self.findChild(QtWidgets.QLineEdit, "confirmPassword")

        if new_pwd.text() == confirm_pwd.text():
            if self.user_manager.change_password(current_pwd.text(), new_pwd.text()):
                current_pwd.setText("")
                new_pwd.setText("")
                confirm_pwd.setText("")
                current_pwd.setStyleSheet("")
                confirm_pwd.setStyleSheet("")
            else:
                self.mark_invalid_input(current_pwd)
        else:
            self.mark_invalid_input(confirm_pwd)

    def on_login_button(self):
        username_input = self.findChild(QtWidgets.QLineEdit, "usernameLineEdit")
        password_input = self.findChild(QtWidgets.QLineEdit, "passwordLineEdit")

        if self.user_manager.exists(username_input.text()):
            if self.user_manager.check_password(password_input.text(), username_input.text()):
                self.on_login(username_input.text())
                password_input.setStyleSheet("")
                username_input.setStyleSheet("")
            else:
                self.mark_invalid_input(password_input)
        else:
            self.mark_invalid_input(username_input)

    def mark_invalid_input(self, widget: QtWidgets.QWidget):
        widget.setStyleSheet("border: 1px solid red; padding-top: 2px; padding-bottom: 2px; border-radius: 2px;")

    def on_login(self, username):
        self.user_manager.set_user(username)
        balance = self.user_manager.get_balance()
        self.findChild(QtWidgets.QLabel, "userInfoBalanceValue").setText("{:.2f}€".format(balance))
        self.findChild(QtWidgets.QLabel, "welcomeLabel").setText("Hi, {}".format(username))
        self.set_login_tab_state(False)
        self.set_user_tab_state(True)
        self.findChild(QtWidgets.QTabWidget, "tabWidget").setCurrentIndex(1)

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
        self.setWindowIcon(QtGui.QIcon("assets/logo.png"))
        self.findChild(QtWidgets.QPushButton, "logoutButton").setIcon(QtGui.QIcon("assets/logout.png"))
        self.findChild(QtWidgets.QPushButton, "stockTablePrevPage").setIcon(QtGui.QIcon("assets/left_arrow.png"))
        self.findChild(QtWidgets.QPushButton, "stockTableNextPage").setIcon(QtGui.QIcon("assets/right_arrow.png"))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
