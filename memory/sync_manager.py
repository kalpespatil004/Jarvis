"""Central realtime synchronization manager for Jarvis memory."""
from __future__ import annotations

import os
import socket
import threading
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from memory import firestore_sync
from memory.local_cache import append_turn, load_sync_metadata, read_cache, save_sync_metadata

_DEVICE_ENV = "JARVIS_DEVICE_ID"
_SYNC_LOCK = threading.RLock()
_STARTED = False
_LISTENER: Any | None = None
_LISTENER_THREAD: threading.Thread | None = None
_DEVICE_ID: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_device_id() -> str:
    global _DEVICE_ID
    if _DEVICE_ID:
        return _DEVICE_ID
    metadata = load_sync_metadata()
    device_id = os.getenv(_DEVICE_ENV) or metadata.get("device_id")
    if not device_id:
        hostname = socket.gethostname() or "desktop"
        device_id = f"desktop-{hostname}-{uuid4().hex[:8]}"
    metadata["device_id"] = str(device_id)
    save_sync_metadata(metadata)
    _DEVICE_ID = str(device_id)
    return _DEVICE_ID


def ensure_turn_identity(turn: dict[str, Any]) -> dict[str, Any]:
    payload = dict(turn)
    timestamp = str(payload.get("timestamp") or payload.get("time") or _now())
    payload["timestamp"] = timestamp
    payload.setdefault("time", timestamp)
    payload.setdefault("device_id", get_device_id())
    payload.setdefault("conversation_id", uuid4().hex)
    return payload


def merge_turn(turn: dict[str, Any]) -> bool:
    if not isinstance(turn, dict) or not turn:
        return False
    payload = ensure_turn_identity(turn)
    added = append_turn(payload)
    if added:
        metadata = load_sync_metadata()
        metadata["device_id"] = get_device_id()
        metadata["last_sync_time"] = _now()
        metadata["last_received_timestamp"] = payload.get("timestamp")
        metadata["last_processed_document"] = payload.get("conversation_id")
        save_sync_metadata(metadata)
    return added


def upload_turn(turn: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(turn, dict) or not turn:
        return None
    payload = ensure_turn_identity(turn)
    uploaded = firestore_sync.push_conversation_turn(payload)
    metadata = load_sync_metadata()
    metadata["device_id"] = get_device_id()
    metadata["last_sync_time"] = _now()
    pending = set(metadata.get("pending_conversation_ids", []))
    conversation_id = str(payload.get("conversation_id"))
    if uploaded:
        pending.discard(conversation_id)
    else:
        pending.add(conversation_id)
    metadata["pending_conversation_ids"] = sorted(pending)
    save_sync_metadata(metadata)
    return payload


def download_latest() -> int:
    metadata = load_sync_metadata()
    since = metadata.get("last_received_timestamp") or metadata.get("last_sync_time")
    turns = firestore_sync.pull_new_conversation_turns(since_timestamp=since)
    merged = 0
    newest = since
    for turn in turns:
        if turn.get("device_id") == get_device_id():
            continue
        if merge_turn(turn):
            merged += 1
        timestamp = turn.get("timestamp") or turn.get("time")
        if timestamp and (not newest or str(timestamp) > str(newest)):
            newest = str(timestamp)
    metadata = load_sync_metadata()
    metadata["device_id"] = get_device_id()
    metadata["last_sync_time"] = _now()
    if newest:
        metadata["last_received_timestamp"] = newest
    save_sync_metadata(metadata)
    return merged


def _on_remote_turn(turn: dict[str, Any]) -> None:
    if turn.get("device_id") == get_device_id():
        return
    merge_turn(turn)


def _listener_worker() -> None:
    global _LISTENER
    while True:
        if _LISTENER is None:
            _LISTENER = firestore_sync.start_realtime_listener(_on_remote_turn, get_device_id())
        threading.Event().wait(30)


def listen_for_updates() -> Any | None:
    global _LISTENER_THREAD
    if _LISTENER_THREAD and _LISTENER_THREAD.is_alive():
        return _LISTENER
    _LISTENER_THREAD = threading.Thread(target=_listener_worker, name="jarvis-firestore-sync", daemon=True)
    _LISTENER_THREAD.start()
    return _LISTENER


def _upload_pending_turns() -> int:
    metadata = load_sync_metadata()
    pending = set(metadata.get("pending_conversation_ids", []))
    if not pending:
        return 0
    uploaded_count = 0
    turns = read_cache().get("conversation_turns", [])
    for turn in turns if isinstance(turns, list) else []:
        if not isinstance(turn, dict):
            continue
        conversation_id = str(turn.get("conversation_id") or turn.get("id") or turn.get("turn_id") or "")
        if conversation_id not in pending:
            continue
        payload = ensure_turn_identity(turn)
        if firestore_sync.push_conversation_turn(payload):
            pending.discard(conversation_id)
            uploaded_count += 1
    metadata["pending_conversation_ids"] = sorted(pending)
    metadata["last_sync_time"] = _now()
    save_sync_metadata(metadata)
    return uploaded_count


def sync_now() -> int:
    with _SYNC_LOCK:
        uploaded = _upload_pending_turns()
        downloaded = download_latest()
        return uploaded + downloaded


def start_sync() -> bool:
    global _STARTED
    with _SYNC_LOCK:
        if _STARTED:
            return True
        get_device_id()
        _upload_pending_turns()
        download_latest()
        listen_for_updates()
        _STARTED = True
        return True
