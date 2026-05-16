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
MAX_CONVERSATION_TURNS = 20

KEY = "conversation_history"
CONVERSATION_TURNS_KEY = "conversation_turns"
SUMMARY_KEY = "conversation_summary"
WORKING_MEMORY_KEY = "working_memory"
LONG_TERM_PREFERENCES_KEY = "user_profile"

CONVERSATIONAL_INTENTS = {
    "chat",
    "question",
    "general_qa",
    "greeting",
}
CONVERSATION_KIND = "conversation"
COMMAND_KINDS = {"action", "command"}


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


def _turn(
    user_text: str,
    assistant_text: str,
    metadata: dict[str, Any] | None = None,
    *,
    timestamp: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "user_text": user_text,
        "assistant_text": assistant_text,
        "time": timestamp or _now(),
        "metadata": metadata or {},
    }
    return item


def _turn_metadata(
    user_metadata: dict[str, Any] | None,
    assistant_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if user_metadata:
        metadata["user"] = _safe_metadata(user_metadata)
    if assistant_metadata:
        metadata["assistant"] = _safe_metadata(assistant_metadata)
    return metadata


def _trim_conversation_turns(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return turns[-MAX_CONVERSATION_TURNS:]


def _legacy_turn_from_messages(
    user_message: dict[str, Any],
    assistant_message: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    user_metadata = user_message.get("metadata")
    assistant_metadata = assistant_message.get("metadata") if isinstance(assistant_message, dict) else None
    if isinstance(user_metadata, dict):
        metadata["user"] = _safe_metadata(user_metadata)
    if isinstance(assistant_metadata, dict):
        metadata["assistant"] = _safe_metadata(assistant_metadata)

    return {
        "user_text": str(user_message.get("text", "")),
        "assistant_text": str(assistant_message.get("text", "")) if isinstance(assistant_message, dict) else "",
        "time": (
            user_message.get("time")
            or (assistant_message.get("time") if isinstance(assistant_message, dict) else None)
            or _now()
        ),
        "metadata": metadata,
    }


def _conversation_turns_from_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    pending_user: dict[str, Any] | None = None
    for message in history:
        if not isinstance(message, dict):
            continue
        if message.get("role") == "user":
            pending_user = message
        elif message.get("role") == "assistant" and pending_user:
            user_metadata = pending_user.get("metadata") if isinstance(pending_user.get("metadata"), dict) else None
            assistant_metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else None
            if _is_conversation_turn(user_metadata, assistant_metadata):
                turns.append(_legacy_turn_from_messages(pending_user, message))
            pending_user = None
    if pending_user:
        user_metadata = pending_user.get("metadata") if isinstance(pending_user.get("metadata"), dict) else None
        if _is_conversation_turn(user_metadata):
            turns.append(_legacy_turn_from_messages(pending_user, None))
    return _trim_conversation_turns(turns)


def _stored_turn_is_conversation(turn: dict[str, Any]) -> bool:
    metadata = turn.get("metadata") if isinstance(turn.get("metadata"), dict) else {}
    user_metadata = metadata.get("user") if isinstance(metadata.get("user"), dict) else None
    assistant_metadata = metadata.get("assistant") if isinstance(metadata.get("assistant"), dict) else None

    # Empty metadata can appear in tests or manually seeded local cache entries;
    # keep those entries unless metadata positively identifies a command/action.
    if user_metadata is None and assistant_metadata is None:
        return True
    return _is_conversation_turn(user_metadata, assistant_metadata)


def _get_conversation_turns(data: dict[str, Any]) -> list[dict[str, Any]]:
    turns = data.get(CONVERSATION_TURNS_KEY)
    if isinstance(turns, list):
        return [
            turn
            for turn in turns
            if isinstance(turn, dict) and _stored_turn_is_conversation(turn)
        ]

    history = data.get(KEY, [])
    if isinstance(history, list):
        return _conversation_turns_from_history(history)
    return []


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


def _metadata_kind(metadata: dict[str, Any] | None) -> str | None:
    if not isinstance(metadata, dict):
        return None
    kind = metadata.get("kind")
    return str(kind).strip().lower() if kind is not None else None


def _is_conversation_turn(
    user_metadata: dict[str, Any] | None,
    assistant_metadata: dict[str, Any] | None = None,
) -> bool:
    """Return True only for normal conversational exchanges worth remembering."""
    user_kind = _metadata_kind(user_metadata)
    assistant_kind = _metadata_kind(assistant_metadata)
    if user_kind == CONVERSATION_KIND or assistant_kind == CONVERSATION_KIND:
        return True
    if user_kind in COMMAND_KINDS or assistant_kind in COMMAND_KINDS:
        return False

    intent = None
    if isinstance(user_metadata, dict):
        intent = user_metadata.get("intent")
    if intent is None and isinstance(assistant_metadata, dict):
        intent = assistant_metadata.get("intent")
    if intent is None:
        return False

    return str(intent).strip().lower() in CONVERSATIONAL_INTENTS


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
    """Persist a complete user/assistant exchange with one cache write.

    Only conversational turns are written to local memory. Because ``write_cache``
    also schedules the remote Firebase/Firestore-style sync, returning before the
    write prevents action commands from being persisted locally or pushed to
    Firebase/Firestore.
    """
    if not _is_conversation_turn(user_metadata, assistant_metadata):
        return

    data = read_cache()
    timestamp = _now()

    turn = _turn(
        user_text,
        assistant_text,
        _turn_metadata(user_metadata, assistant_metadata),
        timestamp=timestamp,
    )
    turns = _get_conversation_turns(data)
    turns.append(turn)
    data[CONVERSATION_TURNS_KEY] = _trim_conversation_turns(turns)

    # Keep the legacy raw message stream for callers that still depend on it.
    history = data.get(KEY, [])
    if not isinstance(history, list):
        history = []
    user_message = _message("user", user_text, user_metadata, timestamp=timestamp)
    assistant_message = _message("assistant", assistant_text, assistant_metadata, timestamp=timestamp)
    history.append(user_message)
    history.append(assistant_message)
    data[KEY] = history

    _capture_preferences(data, user_text)
    _compact_history(data)
    write_cache(data)
    push_conversation_turn(turn)


def get_history() -> list:
    data = read_cache()
    return data.get(KEY, [])


def get_summary() -> str:
    data = read_cache()
    return data.get(SUMMARY_KEY, "")


def get_recent_turns(n: int = DEFAULT_CONTEXT_TURNS) -> list[dict[str, Any]]:
    """Return the last N conversation-only turns for NLU and follow-up resolution."""
    turns = _get_conversation_turns(read_cache())
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
