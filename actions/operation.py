# Undo / Redo mechanics
from enum import Enum


class Action(Enum):
    BUY_STOCKS = 0
    SELL_STOCKS = 1


class Operation:

    def __init__(self, action: Action, stock_name: str, amount: int):
        self.action = action
        self.stock_name = stock_name
        self.amount = amount


class OperationList:

    def __init__(self):
        self.operations = []
        self.un_done = []

    def do(self, operation: Operation):
        self.un_done = []
        self.operations.append(operation)

    def undo(self) -> Operation:
        operation = self.operations.pop()
        self.un_done.append(operation)
        return operation

    def redo(self) -> Operation:
        operation = self.un_done.pop()
        self.operations.append(operation)
        return operation
