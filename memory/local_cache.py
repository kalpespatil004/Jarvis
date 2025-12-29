# memory/local_cache.py
import json
import os
from threading import Lock

DATA_DIR = "database"
CACHE_FILE = os.path.join(DATA_DIR, "cache.json")

_lock = Lock()


def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def read_cache() -> dict:
    _ensure_file()
    with _lock:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def write_cache(data: dict):
    _ensure_file()
    with _lock:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
