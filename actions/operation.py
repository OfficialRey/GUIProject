# Undo / Redo mechanics
from enum import Enum


class Action(Enum):
    BUY_STOCKS = 0
    SELL_STOCKS = 1


class Operation:

    def __init__(self, action: Action, stock_name: str, amount: int):
        self.__action = action
        self.__stock_name = stock_name
        self.__amount = amount
    
    def get_action(self) -> Action:
        return self.__action
    
    def get_stock_name(self) -> str:
        return self.__stock_name
    
    def get_amount(self) -> int:
        return self.__amount


class OperationList:

    def __init__(self):
        self.__operations = []
        self.__un_done = []

    def do(self, operation: Operation):
        self.__un_done = []
        self.__operations.append(operation)

    def undo(self) -> Operation:
        if len(self.__operations):
            operation = self.__operations.pop()
            self.__un_done.append(operation)
            return operation
        return None

    def redo(self) -> Operation:
        if len(self.__un_done):
            operation = self.__un_done.pop()
            self.__operations.append(operation)
            return operation
        return None

    def clear(self):
        self.__operations = []
        self.__un_done = []
