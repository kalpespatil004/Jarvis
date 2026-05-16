"""Firestore-backed conversation sync for Jarvis memory.

Conversation turns are stored under:
    users/{user_id}/conversations/{turn_id}

The Firebase Admin SDK is initialized with the existing service-account file at
``memory/firebase_key.json``. Set ``JARVIS_USER_ID`` to select a cloud user; when
it is not set, Jarvis falls back to a local profile id/name and then ``default``.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


DEFAULT_PULL_LIMIT = 20
USER_ENV_VAR = "JARVIS_USER_ID"

_initialized = False
_firestore_client: Any | None = None
_firestore_module: Any | None = None


def init_firebase() -> Any:
    """Initialize Firebase Admin once and return a Firestore client."""
    global _initialized, _firestore_client, _firestore_module

    if _initialized and _firestore_client is not None:
        return _firestore_client

    import firebase_admin
    from firebase_admin import credentials, firestore

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    key_path = os.path.join(base_dir, "memory", "firebase_key.json")

    cred = credentials.Certificate(key_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    _firestore_module = firestore
    _firestore_client = firestore.client()
    _initialized = True
    return _firestore_client


def _firestore() -> Any:
    """Return the lazily imported firebase_admin.firestore module."""
    if _firestore_module is None:
        init_firebase()
    return _firestore_module


def _safe_user_id(raw_user_id: str | None = None) -> str:
    value = (raw_user_id or os.getenv(USER_ENV_VAR) or _local_profile_user_id() or "default").strip()
    if not value:
        value = "default"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


def _local_profile_user_id() -> str | None:
    """Best-effort local fallback without making local_cache import this module."""
    try:
        from memory.local_cache import read_cache

        profile = read_cache().get("user_profile", {})
        if not isinstance(profile, dict):
            return None
        return profile.get("user_id") or profile.get("id") or profile.get("name")
    except Exception:
        return None


def _conversations_collection(user_id: str | None = None):
    db = init_firebase()
    return db.collection("users").document(_safe_user_id(user_id)).collection("conversations")


def _turn_time(turn: dict[str, Any]) -> str:
    time_value = turn.get("time") or turn.get("created_at")
    if isinstance(time_value, str) and time_value.strip():
        return time_value

    user_message = turn.get("user")
    if isinstance(user_message, dict) and isinstance(user_message.get("time"), str):
        return user_message["time"]

    assistant_message = turn.get("assistant")
    if isinstance(assistant_message, dict) and isinstance(assistant_message.get("time"), str):
        return assistant_message["time"]

    return datetime.now(timezone.utc).isoformat()


def _message_from_turn(turn: dict[str, Any], role: str) -> dict[str, Any] | None:
    legacy_message = turn.get(role)
    if isinstance(legacy_message, dict):
        return legacy_message

    text_key = "user_text" if role == "user" else "assistant_text"
    text = turn.get(text_key)
    if text is None:
        return None

    message: dict[str, Any] = {
        "role": role,
        "text": str(text),
        "time": _turn_time(turn),
    }
    metadata = turn.get("metadata")
    if isinstance(metadata, dict) and isinstance(metadata.get(role), dict):
        message["metadata"] = metadata[role]
    return message


def _conversation_turn_from_cloud(turn: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(turn, dict):
        return None
    if "user_text" in turn or "assistant_text" in turn:
        return {
            "user_text": str(turn.get("user_text", "")),
            "assistant_text": str(turn.get("assistant_text", "")),
            "time": _turn_time(turn),
            "metadata": turn.get("metadata") if isinstance(turn.get("metadata"), dict) else {},
        }

    user_message = turn.get("user")
    assistant_message = turn.get("assistant")
    if not isinstance(user_message, dict):
        return None

    metadata: dict[str, Any] = {}
    if isinstance(user_message.get("metadata"), dict):
        metadata["user"] = user_message["metadata"]
    if isinstance(assistant_message, dict) and isinstance(assistant_message.get("metadata"), dict):
        metadata["assistant"] = assistant_message["metadata"]

    return {
        "user_text": str(user_message.get("text", "")),
        "assistant_text": str(assistant_message.get("text", "")) if isinstance(assistant_message, dict) else "",
        "time": _turn_time(turn),
        "metadata": metadata,
    }


def _turn_document_id(turn: dict[str, Any]) -> str:
    existing_id = turn.get("id") or turn.get("turn_id")
    if existing_id:
        return re.sub(r"[^A-Za-z0-9_.-]", "_", str(existing_id))[:120]

    safe_time = re.sub(r"[^A-Za-z0-9_.-]", "_", _turn_time(turn))[:80]
    return f"{safe_time}_{uuid4().hex[:12]}"


def push_conversation_turn(turn: dict):
    """Push one user/assistant conversation turn to Firestore."""
    if not isinstance(turn, dict) or not turn:
        return

    try:
        payload = dict(turn)
        payload["time"] = _turn_time(payload)
        payload["synced_at"] = _firestore().SERVER_TIMESTAMP

        ref = _conversations_collection().document(_turn_document_id(payload))
        ref.set(payload, merge=True)

    except Exception as exc:
        print("[FIRESTORE PUSH ERROR]", exc)


def pull_last_conversation_turns(limit: int = DEFAULT_PULL_LIMIT) -> list[dict[str, Any]]:
    """Return the latest conversation turns from Firestore in chronological order."""
    try:
        safe_limit = max(1, int(limit or DEFAULT_PULL_LIMIT))
        query = (
            _conversations_collection()
            .order_by("time", direction=_firestore().Query.DESCENDING)
            .limit(safe_limit)
        )
        turns = []
        for snapshot in query.stream():
            turn = snapshot.to_dict() or {}
            turn.setdefault("id", snapshot.id)
            turns.append(turn)
        return list(reversed(turns))

    except Exception as exc:
        print("[FIRESTORE PULL ERROR]", exc)
        return []


def overwrite_local_conversation_from_cloud(limit: int = DEFAULT_PULL_LIMIT) -> bool:
    """Replace local conversation turns with the latest Firestore conversation turns."""
    cloud_turns = pull_last_conversation_turns(limit)
    if not cloud_turns:
        return False

    turns: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    for cloud_turn in cloud_turns:
        turn = _conversation_turn_from_cloud(cloud_turn)
        if turn is not None:
            turns.append(turn)

        user_message = _message_from_turn(cloud_turn, "user")
        if user_message is not None:
            history.append(user_message)

        assistant_message = _message_from_turn(cloud_turn, "assistant")
        if assistant_message is not None:
            history.append(assistant_message)

    if not turns:
        return False

    try:
        from memory.conversation import CONVERSATION_TURNS_KEY, KEY, MAX_CONVERSATION_TURNS
        from memory.local_cache import read_cache, write_cache

        data = read_cache()
        data[CONVERSATION_TURNS_KEY] = turns[-MAX_CONVERSATION_TURNS:]
        if history:
            data[KEY] = history
        write_cache(data)
        return True

    except Exception as exc:
        print("[FIRESTORE LOCAL OVERWRITE ERROR]", exc)
        return False
