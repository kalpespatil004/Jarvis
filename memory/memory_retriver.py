# memory/memory_retriever.py
from memory.conversation import get_history


def recall_last_user_message():
    history = get_history()
    for msg in reversed(history):
        if msg["role"] == "user":
            return msg["text"]
    return None


def recall_recent(n=5):
    return get_history()[-n:]
