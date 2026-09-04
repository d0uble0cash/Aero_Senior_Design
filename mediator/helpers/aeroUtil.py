# File for some functions that could be reused constantly
from datetime import datetime

def tPrint(message: str):
    print(f"{str(datetime.now().time())}: {message}")
