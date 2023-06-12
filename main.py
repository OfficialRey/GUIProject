import sys

from graph.stock_graph import StockPredictionGraph, StockGraph
from logs.log import log_message
from stock_data.stocks import Stonks, Stock
from user.user import User, Database, exists_user, load_user, create_user
from actions.operation import Operation, OperationList, Action
from PyQt5 import uic, QtWidgets, QtGui, QtCore
from worker.table import StockTableItemWorker
from enum import Enum
from re import findall
import time


class StockTableColumn(Enum):
    INFO = 0
    ID = 1
    NAME = 2
    PRICE = 3
    DIFF = 4
    YIELD = 5
    GRAPH = 6


class TabNames(Enum):
    LOGIN = 0
    REGISTER = 1
    USER = 2
    STOCK_LIST = 3
    STOCK_DETAILS = 4
    PORTFOLIO = 5


period_days = {
    "-": 0,
    "7 days": 7,
    "1 month": 30,
    "3 months": 90,
    "6 months": 182,
    "1 year": 365,
    "2 years": 365 * 2,
    "5 years": 365 * 5,
    "10 years": 365 * 10
}


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.worker = None
        uic.loadUi("main.ui", self)

        self.stocks = Stonks()
        self.start_stock_loader_thread()
        self.current_stock: Stock = None
        self.current_user: User = None
        self.set_stock_details(self.stocks.get_stock_names()[0])
        self.operation_list = OperationList()

        self.database = Database()

        self.load_style_sheet("style.qss")
        self.set_tab_state(TabNames.USER.value, False)
        self.set_tab_state(TabNames.REGISTER.value, False)
        self.set_tab_state(TabNames.PORTFOLIO.value, False)
        self.add_functions()
        self.init_stock_table()
        self.init_compare_options()
        self.set_icons()

        self.update_user_tab()

        log_message("GUI launched")

    def load_style_sheet(self, filename):
        with open(filename, "r") as f:
            self.setStyleSheet(f.read().strip())

    def init_compare_options(self):
        compare_options: QtWidgets.QListWidget = self.findChild(QtWidgets.QListWidget, "compareOptions")
        for stock in self.stocks.get_stock_names():
            item: QtWidgets.QListWidgetItem = QtWidgets.QListWidgetItem(stock, compare_options)
            item.setCheckState(False)
            compare_options.addItem(item)

    def start_stock_loader_thread(self):
        self.loader_thread = QtCore.QThread()

        self.worker = StockTableItemWorker(self.stocks)
        self.worker.moveToThread(self.loader_thread)

        self.loader_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.stock_table_append)
        self.worker.finished.connect(self.on_stock_table_load_finished)

        self.worker.finished.connect(self.loader_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.loader_thread.finished.connect(self.loader_thread.deleteLater)

        self.loader_thread.start()
        log_message("Started loading stock details")

    def on_period_changed(self):
        self.set_detail_graph(self.current_stock)

    def on_prediction_period_changed(self):
        self.set_detail_graph(self.current_stock)

    def get_selected_compare_stocks(self) -> list[str]:
        compare_options: QtWidgets.QListWidget = self.findChild(QtWidgets.QListWidget, "compareOptions")
        return [
            compare_options.item(x).text() for x in range(compare_options.count()) if compare_options.item(x).checkState()
        ]

    def set_detail_graph(self, stock):
        compare_graphs = self.get_selected_compare_stocks()

        stock_graph = self.findChild(QtWidgets.QWidget, "historyGraphContainer")
        period_selection: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "graphPeriodSelection")
        predict_selection: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "graphPredictionSelection")
        period = period_days[period_selection.currentText()]
        predict_period = period_days[predict_selection.currentText()]
        layout = stock_graph.layout()
        if layout is not None:
            # Clear layout
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().setParent(None)
        else:
            layout = QtWidgets.QHBoxLayout()
            stock_graph.setLayout(layout)

        compare_x = []
        compare_y = []
        for stock_name in compare_graphs:
            stock = self.stocks.get_stock(stock_name)
            compare_x.append(stock.get_time_stamps(period))
            compare_y.append(stock.get_prices(period))

        graph = StockPredictionGraph(stock.get_time_stamps(period), stock.get_prices(period),
                                     stock.get_prediction(predict_period), compare_x, compare_y)
        layout.addWidget(graph.get_widget())

    def update_portfolio(self):
        total_value = str(round(self.current_user.get_portfolio().get_current_value(self.stocks), 2)) + "€"
        self.findChild(QtWidgets.QLabel, "totalValue").setText(total_value)
        total_predicted_value = str(round(self.current_user.get_portfolio().get_predicted_value(self.stocks), 2)) + "€"
        self.findChild(QtWidgets.QLabel, "predictedValue").setText(total_predicted_value)

        portfolio_stocks = self.current_user.get_portfolio().get_stocks()

        table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "portfolioDetailsTable")
        table.setRowCount(0)

        row = 0
        for stock_name in portfolio_stocks.keys():
            table.insertRow(row)

            stonk = self.stocks.get_stock(stock_name)
            current_value = stonk.get_ask_price()
            predicted_value = stonk.get_prediction(365)[-1]
            print(f"predicted {stock_name} as {predicted_value}")
            profit = round(predicted_value / current_value * 100, 2)
            if profit < 100:
                profit = str((100 - profit) * -1)
            else:
                profit = "+" + str(profit - 100)

            self.set_table_cell_data(row, 1, 1, table, editable=True)
            self.set_table_cell_data(row, 2, stock_name, table)
            self.set_table_cell_data(row, 3, stonk.get_long_name(), table)
            self.set_table_cell_data(row, 4, self.current_user.get_portfolio().get_holding(stock_name), table)
            self.set_table_cell_data(row, 5, current_value, table)
            self.set_table_cell_data(row, 6, str(round(predicted_value, 2)), table)
            self.set_table_cell_data(row, 7, profit, table)

            sell_button = QtWidgets.QPushButton("Sell")
            sell_button.clicked.connect(self.sell_stock)
            table.setCellWidget(row, 0, sell_button)
            row += 1

    def set_stock_details(self, stock_id):
        self.current_stock = self.stocks.get_stock(stock_id)
        stock_name = self.findChild(QtWidgets.QLabel, "stockName")
        stock_name.setText(
            f"<a href={self.current_stock.get_website()}>{self.current_stock.get_long_name()} ({stock_id})</a>")
        stock_price = self.findChild(QtWidgets.QLabel, "stockPrice")
        stock_price.setText(f"{'%.2f' % self.current_stock.get_ask_price()} {self.current_stock.get_currency()}")
        stock_price_diff = self.findChild(QtWidgets.QLabel, "stockPriceDiff")

        self.set_detail_graph(self.current_stock)

        stock_trend = self.current_stock.get_stock_trend(7)
        sign = "+" if stock_trend > 0 else ""
        stock_price_diff.setText(f"{sign}{'{:4.2f}'.format(stock_trend)}%")
        self.findChild(QtWidgets.QLabel, "stockCountry").setText(
            f"{self.current_stock.get_country()}, {self.current_stock.get_city()}")
        self.findChild(QtWidgets.QLabel, "stockCategory").setText(f"{self.current_stock.get_sector()}")
        self.findChild(QtWidgets.QLabel, "stockVolume").setText(f"Volume: {self.current_stock.get_volume()}")
        self.findChild(QtWidgets.QLabel, "stockDividendRate").setText(
            f"Dividend: {round(self.current_stock.get_dividend_yield() * 100, 2)}%")
        self.findChild(QtWidgets.QLabel, "stockDividendYield").setText(
            f"Dividend: {self.current_stock.get_dividend_rate()} {self.current_stock.get_currency()}")
        
        compare_options: QtWidgets.QListWidget = self.findChild(QtWidgets.QListWidget, "compareOptions")
        for x in range(compare_options.count() - 1):
            compare_options.item(x).setCheckState(False)

    def init_stock_table(self):
        stock_table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        stock_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        stock_table.verticalHeader().setDefaultSectionSize(120)

    def on_stock_table_load_finished(self):
        info_label: QtWidgets.QLabel = self.findChild(QtWidgets.QLabel, "stockTableLoadingIndicator")
        info_label.setText("")
        self.findChild(QtWidgets.QTableWidget, "stockDetailTable").setSortingEnabled(True)
        log_message("Finished loading stock details")

    def stock_table_append(self, stock: Stock):
        stock_table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        price_filter_min = self.findChild(QtWidgets.QSlider, "stockPriceFilter")
        price_filter_max = self.findChild(QtWidgets.QSlider, "stockPriceFilter2")

        if stock.get_ask_price() > price_filter_min.maximum():
            new_max = int(stock.get_ask_price()) + 2
            price_filter_min.setMaximum(new_max)
            price_filter_max.setMaximum(new_max)

        stock_trend = stock.get_stock_trend(28)
        stock_graph = StockGraph(stock.get_time_stamps(28), stock.get_prices(28))
        sign = "+" if stock_trend > 0 else ""
        icon = QtGui.QIcon("assets/info_logo.png")
        info_widget = QtWidgets.QPushButton()
        info_widget.setIcon(icon)
        info_widget.clicked.connect(self.show_stock_info)

        i = stock_table.rowCount()
        stock_table.insertRow(i)

        stock_table.setCellWidget(i, StockTableColumn.INFO.value, info_widget)
        self.set_table_cell_data(i, StockTableColumn.ID.value, stock.get_name())
        self.set_table_cell_data(i, StockTableColumn.NAME.value, stock.get_long_name())
        self.set_table_cell_data(i, StockTableColumn.PRICE.value, stock.get_ask_price())
        self.set_table_cell_data(i, StockTableColumn.DIFF.value, f"{sign}{'{:4.2f}'.format(stock_trend)}%")
        stock_table.setCellWidget(i, StockTableColumn.GRAPH.value, stock_graph.get_widget())
        self.set_table_cell_data(i, StockTableColumn.YIELD.value, round(stock.get_dividend_yield() * 100, 4))

        self.on_search_changed()

    def set_table_cell_data(self, row, col, value, widget: QtWidgets.QTableWidget=None, editable=False):
        if not widget:
            widget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        item = widget.item(row, col)
        if not item:
            item = QtWidgets.QTableWidgetItem()
            widget.setItem(row, col, item)
        item.setData(QtCore.Qt.ItemDataRole.DisplayRole, value)
        if not editable:
            item.setFlags(QtCore.Qt.ItemIsEnabled)

    def get_table_cell_data(self, row, col):
        stock_table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        item = stock_table.item(row, col)
        if not item:
            return ""
        return item.data(QtCore.Qt.ItemDataRole.DisplayRole)

    def show_stock_info(self):
        table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        row = table.currentRow()

        stock_id = self.get_table_cell_data(row, StockTableColumn.ID.value)
        self.set_stock_details(stock_id)

        tab_widget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        tab_widget.setCurrentIndex(TabNames.STOCK_DETAILS.value)

    def sell_stock(self):
        if not self.current_user:
            return

        table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "portfolioDetailsTable")
        row = table.currentRow()
        stock_name = table.item(row, 2).data(QtCore.Qt.ItemDataRole.DisplayRole)
        sell_amount = table.item(row, 1).data(QtCore.Qt.ItemDataRole.DisplayRole)
        
        self.current_user.get_portfolio().sell_stock(stock_name, self.stocks.get_stock(stock_name).get_ask_price(), sell_amount)
        self.update_portfolio()
        self.update_user_tab()
        self.current_user.save_user()

    def buy_stock(self):
        if self.current_user is not None:
            stock_price = self.current_stock.get_ask_price()
            balance = self.current_user.get_balance_euros()
            port_folio = self.current_user.get_portfolio()
            amount = int(self.findChild(QtWidgets.QSpinBox, "buyStockAmount").text())
            final_price = stock_price * amount
            if balance >= final_price:
                port_folio.buy_stock(self.current_stock.get_name(), self.current_stock.get_ask_price(), amount)
                self.current_user.save_user()
                self.update_user_tab()
                self.update_portfolio()

                self.operation_list.do(Operation(Action.BUY_STOCKS, self.current_stock.get_name(), amount))

                message_box = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Icon.Information, "Success", "Stock added to your portfolio.")
                message_box.exec()
            else:
                message_box = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Icon.Warning, "Warning",
                    "You don't have enough money. Consider selling some of your stock.")
                message_box.exec()
        else:
            message_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning, "Warning", "Please log in to use this feature.")
            message_box.exec()

    def undo(self):
        operation = self.operation_list.undo()
        if not operation:
            return

        portfolio = self.current_user.get_portfolio()
        stock_name = operation.get_stock_name()
        if operation.get_action == Action.SELL_STOCKS:
            portfolio.buy_stock(stock_name, self.stocks.get_stock(stock_name).get_ask_price(), operation.get_amount())
        else:
            portfolio.sell_stock(stock_name, self.stocks.get_stock(stock_name).get_ask_price(), operation.get_amount())

        self.current_user.save_user()
        self.update_user_tab()
        self.update_portfolio()

    def redo(self):
        operation = self.operation_list.redo()
        if not operation:
            return

        portfolio = self.current_user.get_portfolio()
        stock_name = operation.get_stock_name()
        if operation.get_action == Action.SELL_STOCKS:
            portfolio.sell_stock(stock_name, self.stocks.get_stock(stock_name).get_ask_price(), operation.get_amount())
        else:
            portfolio.buy_stock(stock_name, self.stocks.get_stock(stock_name).get_ask_price(), operation.get_amount())

        self.current_user.save_user()
        self.update_user_tab()
        self.update_portfolio()

    def add_functions(self):
        self.findChild(QtWidgets.QLineEdit, "stockNameSearch").textChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QSlider, "stockPriceFilter").valueChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QSlider, "stockPriceFilter2").valueChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QCheckBox, "positiveTrendsCheck").stateChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QCheckBox, "negativeTrendsCheck").stateChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QSlider, "stockYieldFilter").valueChanged.connect(self.on_search_changed)
        self.findChild(QtWidgets.QPushButton, "loginButton").clicked.connect(self.on_login_button)
        self.findChild(QtWidgets.QPushButton, "registerButton").clicked.connect(self.on_register_button)
        self.findChild(QtWidgets.QPushButton, "registerButton_2").clicked.connect(self.on_register_confirm)
        self.findChild(QtWidgets.QPushButton, "cancelRegister").clicked.connect(self.on_register_cancel)
        self.findChild(QtWidgets.QAction, "actionExit").triggered.connect(self.on_exit)
        self.findChild(QtWidgets.QAction, "actionStyleSheet").triggered.connect(
            lambda: self.load_style_sheet("style.qss"))
        self.findChild(QtWidgets.QAction, "actionUndo").triggered.connect(self.undo)
        self.findChild(QtWidgets.QAction, "actionRedo").triggered.connect(self.redo)
        self.findChild(QtWidgets.QPushButton, "logoutButton").clicked.connect(self.logout)
        self.findChild(QtWidgets.QPushButton, "confirmChangePassword").clicked.connect(self.change_password)
        self.findChild(QtWidgets.QComboBox, "graphPeriodSelection").currentIndexChanged.connect(self.on_period_changed)
        self.findChild(QtWidgets.QComboBox, "graphPredictionSelection").currentIndexChanged.connect(
            self.on_prediction_period_changed)
        self.findChild(QtWidgets.QPushButton, "buyStockButton").clicked.connect(self.buy_stock)
        self.findChild(QtWidgets.QListWidget, "compareOptions").itemClicked.connect(
            lambda: self.set_detail_graph(self.current_stock))

    def set_page_button_state(self, state: bool):
        prev = self.findChild(QtWidgets.QPushButton, "stockTablePrevPage")
        next = self.findChild(QtWidgets.QPushButton, "stockTableNextPage")
        prev.setEnabled(state)
        next.setEnabled(state)

    def on_exit(self):
        self.close()

    def change_password(self):
        if self.current_user is None:
            return

        current_pwd = self.findChild(QtWidgets.QLineEdit, "currentPassword")
        new_pwd = self.findChild(QtWidgets.QLineEdit, "newPassword")
        confirm_pwd = self.findChild(QtWidgets.QLineEdit, "confirmPassword")

        if not self.current_user.check_password(current_pwd.text()):
            self.mark_invalid_input(current_pwd)
            return

        if new_pwd.text() == confirm_pwd.text():
            if self.current_user.change_password(new_pwd.text()):
                current_pwd.setText("")
                new_pwd.setText("")
                confirm_pwd.setText("")
                current_pwd.setStyleSheet("")
                confirm_pwd.setStyleSheet("")
        else:
            self.mark_invalid_input(confirm_pwd)

    def on_register_confirm(self):
        username = self.findChild(QtWidgets.QLineEdit, "registerUsername")
        password = self.findChild(QtWidgets.QLineEdit, "registerPassword")
        confirm_pwd = self.findChild(QtWidgets.QLineEdit, "registerPasswordConfirm")

        if exists_user(username.text(), self.database) or username.text() == "":
            self.mark_invalid_input(username)
            return

        if password.text() == "" or password.text() != confirm_pwd.text():
            self.mark_invalid_input(confirm_pwd)
            return

        create_user(username.text(), password.text(), self.database)
        user = load_user(username.text(), password.text(), self.database)
        self.login(user)

        confirm_pwd.setStyleSheet("")
        password.setStyleSheet("")
        username.setStyleSheet("")
        username.setText("")
        password.setText("")
        confirm_pwd.setText("")
        self.set_tab_state(TabNames.REGISTER.value, False)
        self.findChild(QtWidgets.QTabWidget, "tabWidget").setCurrentIndex(TabNames.USER.value)

    def on_register_button(self):
        self.set_tab_state(TabNames.REGISTER.value, True)
        self.set_tab_state(TabNames.LOGIN.value, False)

    def on_register_cancel(self):
        self.set_tab_state(TabNames.REGISTER.value, False)
        self.set_tab_state(TabNames.LOGIN.value, True)

        tabWidget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        tabWidget.setCurrentIndex(TabNames.LOGIN.value)

    def on_login_button(self):
        username_input = self.findChild(QtWidgets.QLineEdit, "usernameLineEdit")
        password_input = self.findChild(QtWidgets.QLineEdit, "passwordLineEdit")

        if exists_user(username_input.text(), self.database):
            temp_user = load_user(username_input.text(), password_input.text(), self.database)
            if temp_user is not None:
                self.login(temp_user)
            else:
                self.mark_invalid_input(password_input)
        else:
            self.mark_invalid_input(username_input)

    def mark_invalid_input(self, widget: QtWidgets.QWidget):
        widget.setStyleSheet("border: 1px solid red; padding-top: 2px; padding-bottom: 2px; border-radius: 2px;")

    def update_user_tab(self):
        welcome_label = self.findChild(QtWidgets.QLabel, "welcomeLabel")
        balance_value = self.findChild(QtWidgets.QLabel, "userInfoBalanceValue")
        portfolio_value = self.findChild(QtWidgets.QLabel, "userInfoPortfolioValue")
        balance_label = self.findChild(QtWidgets.QLabel, "userInfoBalance")
        portfolio_label = self.findChild(QtWidgets.QLabel, "userInfoPortfolio")
        logout = self.findChild(QtWidgets.QPushButton, "logoutButton")
        if self.current_user is not None:
            self.set_tab_state(TabNames.LOGIN.value, False)
            self.set_tab_state(TabNames.USER.value, True)
            self.set_tab_state(TabNames.PORTFOLIO.value, True)

            user_balance = self.current_user.get_balance_euros()

            welcome_label.setText("Hi, {}".format(self.current_user.get_user_name()))
            balance_value.setText(str(user_balance))
            portfolio_value.setText(str(self.current_user.get_portfolio().get_current_value(self.stocks)))

            balance_value.show()
            balance_label.show()
            portfolio_value.show()
            portfolio_label.show()

            logout.show()
        else:
            self.set_tab_state(TabNames.LOGIN.value, True)
            self.set_tab_state(TabNames.USER.value, False)
            self.set_tab_state(TabNames.PORTFOLIO.value, False)

            welcome_label.setText("Hi, Guest")
            balance_value.hide()
            balance_label.hide()
            portfolio_value.hide()
            portfolio_label.hide()

            logout.hide()

    def login(self, user: User):
        self.current_user = user
        self.findChild(QtWidgets.QLineEdit, "usernameLineEdit").setText("")
        self.findChild(QtWidgets.QLineEdit, "passwordLineEdit").setText("")
        self.update_user_tab()
        self.update_portfolio()

    def logout(self):
        self.current_user = None
        self.operation_list.clear()
        self.update_user_tab()

    def set_tab_state(self, tab_id, state):
        tab_widget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        tab_widget.setTabEnabled(tab_id, state)
        tab_widget.setStyleSheet(tab_widget.styleSheet())

    def on_search_changed(self):
        search = self.findChild(QtWidgets.QLineEdit, "stockNameSearch").text()
        value_lower = self.findChild(QtWidgets.QSlider, "stockPriceFilter").value()
        value_upper = self.findChild(QtWidgets.QSlider, "stockPriceFilter2").value()
        positive_check = self.findChild(QtWidgets.QCheckBox, "positiveTrendsCheck").isChecked()
        negative_check = self.findChild(QtWidgets.QCheckBox, "negativeTrendsCheck").isChecked()
        yield_slider_value = self.findChild(QtWidgets.QSlider, "stockYieldFilter").value()

        if value_lower > value_upper:
            slider = self.findChild(QtWidgets.QSlider, "stockPriceFilter2")
            slider.setValue(value_lower + 1)
            value_upper += 1
        if value_upper < value_lower:
            slider = self.findChild(QtWidgets.QSlider, "stockPriceFilter")
            slider.setValue(value_upper - 1)
            value_lower -= 1

        stock_table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        for i in range(stock_table.rowCount()):
            name = str(self.get_table_cell_data(i, StockTableColumn.NAME.value))
            price = self.get_table_cell_data(i, StockTableColumn.PRICE.value)
            diff = self.get_table_cell_data(i, StockTableColumn.DIFF.value)
            stock_yield = self.get_table_cell_data(i, StockTableColumn.YIELD.value)
            if search.lower() not in name.lower() or price < value_lower or price > value_upper or \
                    ("+" in diff and not positive_check) or (
                    "-" in diff and not negative_check) or stock_yield < yield_slider_value:
                stock_table.hideRow(i)
            else:
                stock_table.showRow(i)

    def set_icons(self):
        self.setWindowIcon(QtGui.QIcon("assets/logo.png"))
        self.findChild(QtWidgets.QPushButton, "logoutButton").setIcon(QtGui.QIcon("assets/logout.png"))
        self.findChild(QtWidgets.QPushButton, "stockTablePrevPage").setIcon(QtGui.QIcon("assets/left_arrow.png"))
        self.findChild(QtWidgets.QPushButton, "stockTableNextPage").setIcon(QtGui.QIcon("assets/right_arrow.png"))


if __name__ == "__main__":
    log_message("Program launched")
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
