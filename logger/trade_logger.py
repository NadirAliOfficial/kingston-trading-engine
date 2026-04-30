import logging
import os
from datetime import datetime

_DATE = datetime.now().strftime("%Y%m%d")


def _make_logger(name, filename):
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    fh = logging.FileHandler(f"logs/{filename}")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def get_signal_logger():
    return _make_logger("signals", f"signals_{_DATE}.log")


def get_trade_logger():
    return _make_logger("trades", f"trades_{_DATE}.log")
