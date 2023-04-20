import pandas as pd

SAVE_FILE = "log.txt"


def set_save_file(save_file: str):
    global SAVE_FILE
    if save_file is None:
        save_file = SAVE_FILE
    SAVE_FILE = save_file


def log_message(message: str):
    time_stamp = pd.Timestamp.now()
    message = message.replace("\n", "")
    message = f"{time_stamp} - Log: {message}\n"
    print(message, end="")
    _append_log(message)


def _append_log(message: str):
    with open(SAVE_FILE, "a+") as file:
        file.write(message)
        file.close()
