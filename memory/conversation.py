# memory/conversation.py
from memory.local_cache import read_cache, write_cache
from datetime import datetime

MAX_HISTORY = 20
KEY = "conversation_history"


def add_message(role: str, text: str):
    data = read_cache()
    history = data.get(KEY, [])

    history.append({
        "role": role,
        "text": text,
        "time": datetime.now().isoformat()
    })

    history = history[-MAX_HISTORY:]
    data[KEY] = history
    write_cache(data)


def get_history() -> list:
    data = read_cache()
    return data.get(KEY, [])
