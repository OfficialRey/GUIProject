import math
from typing import List


class StockPage:

    def __init__(self, stock_names: List[str], page_contents: int):
        self.page_index = 0
        self.page_contents = page_contents
        self.stock_names = stock_names

    def update_stock_names(self, stock_names: str):
        self.page_index = 0
        self.stock_names = stock_names

    def get_page(self) -> List[str]:
        return self.stock_names[self.page_contents * self.page_index: self.page_contents * (self.page_index + 1):]

    def get_page_by_index(self, index: int):
        if index > self.get_max_pages():
            raise IndexError(f"Invalid index {index}: Max index is {self.get_max_pages()}")

        self.page_index = index
        return self.get_page()

    def previous_page(self):
        self.page_index -= 1
        if self.page_index < 0:
            self.page_index = 0
        return self.get_page()

    def next_page(self):
        self.page_index += 1
        if self.page_index > self.get_max_pages():
            self.page_index -= 1
        return self.get_page()

    def get_page_index(self):
        return self.page_index

    def get_page_size(self):
        return self.page_contents

    def get_max_pages(self):
        return math.ceil(len(self.stock_names) / self.page_contents) - 1
