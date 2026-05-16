# memory/conversation.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from memory.firestore_sync import push_conversation_turn
from memory.local_cache import read_cache, write_cache

# Keep enough verbatim context for follow-ups while compacting older sessions.
MAX_RECENT_MESSAGES = 40
COMPACT_AFTER_MESSAGES = 60
DEFAULT_CONTEXT_TURNS = 6

KEY = "conversation_history"
SUMMARY_KEY = "conversation_summary"
WORKING_MEMORY_KEY = "working_memory"
LONG_TERM_PREFERENCES_KEY = "user_profile"


def _now() -> str:
    return datetime.now().isoformat()


def _message(
    role: str,
    text: str,
    metadata: dict[str, Any] | None = None,
    *,
    timestamp: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "role": role,
        "text": text,
        "time": timestamp or _now(),
    }
    if metadata:
        item["metadata"] = _safe_metadata(metadata)
    return item


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if key.startswith("_"):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        elif isinstance(value, (list, tuple)):
            safe[key] = [v for v in value if isinstance(v, (str, int, float, bool)) or v is None]
        elif isinstance(value, dict):
            safe[key] = {
                str(k): v
                for k, v in value.items()
                if isinstance(v, (str, int, float, bool)) or v is None
            }
    return safe


def add_message(role: str, text: str, metadata: dict[str, Any] | None = None):
    """Append one message and compact old history when needed."""
    data = read_cache()
    history = data.get(KEY, [])
    history.append(_message(role, text, metadata))
    data[KEY] = history
    _compact_history(data)
    write_cache(data)


def add_turn(
    user_text: str,
    assistant_text: str,
    *,
    user_metadata: dict[str, Any] | None = None,
    assistant_metadata: dict[str, Any] | None = None,
):
    """Persist a complete user/assistant exchange with one cache write and Firestore sync."""
    data = read_cache()
    history = data.get(KEY, [])
    timestamp = _now()
    user_message = _message("user", user_text, user_metadata, timestamp=timestamp)
    assistant_message = _message("assistant", assistant_text, assistant_metadata, timestamp=timestamp)
    history.append(user_message)
    history.append(assistant_message)
    data[KEY] = history
    _capture_preferences(data, user_text)
    _compact_history(data)
    write_cache(data)
    push_conversation_turn({"time": timestamp, "user": user_message, "assistant": assistant_message})


def get_history() -> list:
    data = read_cache()
    return data.get(KEY, [])


def get_summary() -> str:
    data = read_cache()
    return data.get(SUMMARY_KEY, "")


def get_recent_turns(n: int = DEFAULT_CONTEXT_TURNS) -> list[dict[str, Any]]:
    """Return the last N user/assistant turns for NLU and follow-up resolution."""
    history = get_history()
    turns: list[dict[str, Any]] = []
    pending_user: dict[str, Any] | None = None
    for message in history:
        if message.get("role") == "user":
            pending_user = message
        elif message.get("role") == "assistant" and pending_user:
            turns.append({"user": pending_user, "assistant": message})
            pending_user = None
    if pending_user:
        turns.append({"user": pending_user, "assistant": None})
    return turns[-max(0, n):]


def get_nlu_context(n: int = DEFAULT_CONTEXT_TURNS) -> dict[str, Any]:
    data = read_cache()
    return {
        "summary": data.get(SUMMARY_KEY, ""),
        "recent_turns": get_recent_turns(n),
        "working_memory": data.get(WORKING_MEMORY_KEY, {}),
        "preferences": data.get(LONG_TERM_PREFERENCES_KEY, {}),
    }


def set_working_memory(**kwargs):
    data = read_cache()
    working = data.get(WORKING_MEMORY_KEY, {})
    working.update(kwargs)
    working["updated_at"] = _now()
    data[WORKING_MEMORY_KEY] = working
    write_cache(data)


def clear_working_memory():
    data = read_cache()
    data[WORKING_MEMORY_KEY] = {}
    write_cache(data)


def _compact_history(data: dict[str, Any]):
    history = data.get(KEY, [])
    if len(history) <= COMPACT_AFTER_MESSAGES:
        return

    old = history[:-MAX_RECENT_MESSAGES]
    recent = history[-MAX_RECENT_MESSAGES:]
    previous_summary = data.get(SUMMARY_KEY, "").strip()
    data[SUMMARY_KEY] = _summarize_messages(previous_summary, old)
    data[KEY] = recent


def _summarize_messages(previous_summary: str, messages: list[dict[str, Any]]) -> str:
    user_count = sum(1 for m in messages if m.get("role") == "user")
    assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
    intent_counts: dict[str, int] = {}
    highlights: list[str] = []

    for message in messages:
        metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
        intent = metadata.get("intent")
        if intent:
            intent_counts[str(intent)] = intent_counts.get(str(intent), 0) + 1
        if message.get("role") == "user" and len(highlights) < 8:
            text = str(message.get("text", "")).strip()
            if text:
                highlights.append(text[:120])

    parts: list[str] = []
    if previous_summary:
        parts.append(previous_summary)
    parts.append(
        f"Compacted {len(messages)} older messages ({user_count} user, {assistant_count} assistant)."
    )
    if intent_counts:
        top = sorted(intent_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        parts.append("Common intents: " + ", ".join(f"{name} x{count}" for name, count in top) + ".")
    if highlights:
        parts.append("Older user requests included: " + "; ".join(highlights) + ".")
    return "\n".join(parts)[-4000:]


def _capture_preferences(data: dict[str, Any], user_text: str):
    """Store simple durable preferences separately from short-term dialogue state."""
    text = user_text.strip()
    lowered = text.lower()
    markers = ("i prefer ", "i like ", "remember that i ", "my preference is ")
    if not any(marker in lowered for marker in markers):
        return

    profile = data.get(LONG_TERM_PREFERENCES_KEY, {})
    preferences = profile.get("preferences", [])
    if not isinstance(preferences, list):
        preferences = []
    if text not in preferences:
        preferences.append(text)
    profile["preferences"] = preferences[-50:]
    profile["updated_at"] = _now()
    data[LONG_TERM_PREFERENCES_KEY] = profile
