import json
import os
from datetime import datetime, timezone
from threading import Lock
from typing import Any

DATA_DIR = "database"
CACHE_FILE = os.path.join(DATA_DIR, "cache.json")
SYNC_FILE = os.path.join(DATA_DIR, "sync.json")
CONVERSATION_TURNS_KEY = "conversation_turns"
CONVERSATION_HISTORY_KEY = "conversation_history"
MAX_CONVERSATION_TURNS = 20
MAX_HISTORY_MESSAGES = 40

_lock = Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _ensure_sync_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SYNC_FILE):
        with open(SYNC_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def read_cache() -> dict:
    _ensure_file()
    with _lock:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {}
            return data if isinstance(data, dict) else {}


def write_cache(data: dict):
    _ensure_file()

    with _lock:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def _turn_timestamp(turn: dict[str, Any]) -> str:
    value = turn.get("timestamp") or turn.get("time") or turn.get("created_at")
    return str(value) if value else _now()


def _turn_id(turn: dict[str, Any]) -> str | None:
    value = turn.get("conversation_id") or turn.get("id") or turn.get("turn_id")
    return str(value) if value else None


def has_turn(turn_or_id: dict[str, Any] | str) -> bool:
    conversation_id = _turn_id(turn_or_id) if isinstance(turn_or_id, dict) else str(turn_or_id)
    if not conversation_id:
        return False
    data = read_cache()
    turns = data.get(CONVERSATION_TURNS_KEY, [])
    return any(isinstance(turn, dict) and _turn_id(turn) == conversation_id for turn in turns)


def _messages_from_turn(turn: dict[str, Any]) -> list[dict[str, Any]]:
    timestamp = _turn_timestamp(turn)
    metadata = turn.get("metadata") if isinstance(turn.get("metadata"), dict) else {}
    messages: list[dict[str, Any]] = []
    if turn.get("user_text") is not None:
        user_message: dict[str, Any] = {"role": "user", "text": str(turn.get("user_text", "")), "time": timestamp}
        if isinstance(metadata.get("user"), dict):
            user_message["metadata"] = metadata["user"]
        messages.append(user_message)
    if turn.get("assistant_text") is not None:
        assistant_message: dict[str, Any] = {"role": "assistant", "text": str(turn.get("assistant_text", "")), "time": timestamp}
        if isinstance(metadata.get("assistant"), dict):
            assistant_message["metadata"] = metadata["assistant"]
        messages.append(assistant_message)
    return messages


def append_turn(turn: dict[str, Any], *, update_history: bool = True) -> bool:
    if not isinstance(turn, dict) or not turn:
        return False
    data = read_cache()
    turns = data.get(CONVERSATION_TURNS_KEY, [])
    if not isinstance(turns, list):
        turns = []

    conversation_id = _turn_id(turn)
    if conversation_id and any(isinstance(existing, dict) and _turn_id(existing) == conversation_id for existing in turns):
        return False

    normalized = dict(turn)
    normalized["timestamp"] = _turn_timestamp(normalized)
    normalized.setdefault("time", normalized["timestamp"])
    turns.append(normalized)
    turns.sort(key=_turn_timestamp)
    data[CONVERSATION_TURNS_KEY] = turns[-MAX_CONVERSATION_TURNS:]

    if update_history:
        history = data.get(CONVERSATION_HISTORY_KEY, [])
        if not isinstance(history, list):
            history = []
        history.extend(_messages_from_turn(normalized))
        data[CONVERSATION_HISTORY_KEY] = history[-MAX_HISTORY_MESSAGES:]

    write_cache(data)
    return True


def merge_turns(turns: list[dict[str, Any]]) -> int:
    merged = 0
    for turn in turns or []:
        if append_turn(turn):
            merged += 1
    return merged


def load_sync_metadata() -> dict[str, Any]:
    _ensure_sync_file()
    with _lock:
        with open(SYNC_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {}
            return data if isinstance(data, dict) else {}


def save_sync_metadata(metadata: dict[str, Any]):
    _ensure_sync_file()
    with _lock:
        with open(SYNC_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata or {}, f, indent=2)
