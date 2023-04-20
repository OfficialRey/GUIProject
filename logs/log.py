import pandas as pd


class Logger:

    def log_message(self, message: str):
        time_stamp = pd.Timestamp.now()
        print(f"{time_stamp} - Log: {message}")
