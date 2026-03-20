import os
import firebase_admin
from firebase_admin import credentials, db

_initialized = False


# =========================
# INIT
# =========================
def init_firebase():
    global _initialized

    if _initialized:
        return

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    KEY_PATH = os.path.join(BASE_DIR, "memory", "firebase_key.json")

    cred = credentials.Certificate(KEY_PATH)

    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://fir-tutorial-11319-default-rtdb.firebaseio.com/"
    })

    _initialized = True


# =========================
# FILTER LOGIC
# =========================
def is_meaningful(text: str) -> bool:
    text = text.lower().strip()

    if len(text.split()) <= 2:
        return False

    ignore_keywords = [
        "open", "play", "stop", "exit", "shutdown",
        "time", "date"
    ]

    if any(word in text for word in ignore_keywords):
        return False

    return True


def filter_sync_data(data: dict) -> dict:
    history = data.get("conversation_history", [])

    meaningful_questions = [
        {
            "text": msg["text"],
            "time": msg["time"]
        }
        for msg in history
        if msg.get("role") == "user" and is_meaningful(msg.get("text", ""))
    ]

    meaningful_questions = meaningful_questions[-10:]

    return {
        "user_profile": data.get("user_profile", {}),
        "important_questions": meaningful_questions
    }


# =========================
# PUSH
# =========================
def push_memory(data: dict):
    try:
        init_firebase()

        filtered = filter_sync_data(data)

        if not filtered:
            return

        ref = db.reference("jarvis/memory")
        ref.set(filtered)

    except Exception as e:
        print("[FIREBASE PUSH ERROR]", e)


# =========================
# PULL
# =========================
def pull_memory():
    try:
        init_firebase()

        ref = db.reference("jarvis/memory")
        return ref.get() or {}

    except Exception as e:
        print("[FIREBASE PULL ERROR]", e)
        return {}