import sys
import json
from PyQt5 import uic, QtWidgets
from stock_data.stocks import Stonks
from PyQt5 import uic, QtWidgets, QtGui, QtCore
import hashlib


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self.current_user = ""

        super(MainWindow, self).__init__()
        uic.loadUi("main.ui", self)

        self.stocks = Stonks()

        with open("style.css") as f:
             self.setStyleSheet(f.read().strip())

        with open("users.json") as f:
            self.user_list = json.load(f)

        self.set_user_tab_state(False)
        self.add_functions()
        self.add_stock_table()
        self.set_icons()

    def add_stock_table(self):
        stock_table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")
        stock_names = self.stocks.get_stock_names()
        for i in range(len(stock_names)):
            stock_info = self.stocks.get_stock_info(stock_names[i])
            stock_table.insertRow(stock_table.rowCount())
            stock_table.setCellWidget(i, 0, QtWidgets.QLabel(f"{stock_info.long_name} ({stock_names[i]})"))
            stock_table.setCellWidget(i, 1, QtWidgets.QLabel(f"{stock_info.ask_price} {stock_info.currency}"))
            stock_table.setCellWidget(i, 2, QtWidgets.QLabel(f"(+0.00%)"))
            stock_table.setCellWidget(i, 3, QtWidgets.QLabel("[graph]"))

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
        stock_table: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, "stockDetailTable")

        if value_lower > value_upper:
             slider = self.findChild(QtWidgets.QSlider, "stockPriceFilter2")
             slider.setValue(value_lower + 1)
             value_upper += 1
        if value_upper < value_lower:
             slider = self.findChild(QtWidgets.QSlider, "stockPriceFilter")
             slider.setValue(value_upper - 1)
             value_lower -= 1

        for i in range(stock_table.rowCount()):
            stock_name = stock_table.cellWidget(i, 0).text()
            try:
                stock_price = float(stock_table.cellWidget(i, 1).text()[:-4])
            except ValueError:
                stock_price = 0.0
            stock_trend = float(stock_table.cellWidget(i, 2).text()[1:-2])
            if search.lower() not in stock_name.lower() or \
                value_lower > stock_price or value_upper < stock_price or \
                (stock_trend >= 0 and not positive_check) or \
                (stock_trend <= 0 and not negative_check):
                    stock_table.hideRow(i)
            else:
                stock_table.showRow(i)
    
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