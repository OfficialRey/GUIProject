import math
from typing import List


class StockPage:

    def __init__(self, stock_names: List[str], page_contents: int):
        self.page = 0
        self.page_contents = page_contents
        self.stock_names = stock_names

    def get_page(self) -> List[str]:
        return self.stock_names[self.page_contents * self.page: self.page_contents * (self.page + 1):]

    def get_page_by_index(self, index: int):
        if index > self.get_max_pages():
            raise IndexError(f"Invalid index {index}: Max index is {self.get_max_pages()}")

        self.page = index
        return self.get_page()

    def previous_page(self):
        self.page -= 1
        if self.page < 0:
            self.page = 0
        return self.get_page()

    def next_page(self):
        self.page += 1
        if self.page > self.get_max_pages():
            self.page -= 1
        return self.get_page()

    def get_max_pages(self):
        return math.ceil(len(self.stock_names) / self.page_contents) - 1
