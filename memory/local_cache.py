import json
import os
import threading
from threading import Lock
from memory.firebase_sync import push_memory

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


def async_push(data):
    thread = threading.Thread(target=push_memory, args=(data,))
    thread.daemon = True
    thread.start()


def write_cache(data: dict):
    _ensure_file()

    with _lock:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    async_push(data)