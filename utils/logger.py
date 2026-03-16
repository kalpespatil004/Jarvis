"""
utils/logger.py  –  Jarvis logging system
"""

import logging
import os
from datetime import datetime

try:
    from config import LOGS_DIR, DEBUG_MODE
except ImportError:
    LOGS_DIR   = "logs"
    DEBUG_MODE = False

os.makedirs(LOGS_DIR, exist_ok=True)

_log_file = os.path.join(LOGS_DIR, f"jarvis_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)


def get_logger(name: str = "Jarvis") -> logging.Logger:
    return logging.getLogger(name)


# Default logger
logger = get_logger("Jarvis")
