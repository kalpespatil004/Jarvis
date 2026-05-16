import importlib
import sys
import types


def _import_conversation(monkeypatch):
    firebase_admin = types.ModuleType("firebase_admin")
    firebase_admin.credentials = types.SimpleNamespace(Certificate=lambda path: object())
    firebase_admin.db = types.SimpleNamespace(reference=lambda path: object())
    firebase_admin.initialize_app = lambda *args, **kwargs: None

    monkeypatch.setitem(sys.modules, "firebase_admin", firebase_admin)
    monkeypatch.setitem(sys.modules, "firebase_admin.credentials", firebase_admin.credentials)
    monkeypatch.setitem(sys.modules, "firebase_admin.db", firebase_admin.db)
    sys.modules.pop("memory.firebase_sync", None)
    sys.modules.pop("memory.local_cache", None)
    sys.modules.pop("memory.conversation", None)
    return importlib.import_module("memory.conversation")


def test_add_turn_persists_chat_intent(monkeypatch):
    conversation = _import_conversation(monkeypatch)
    writes = []

    monkeypatch.setattr(conversation, "read_cache", lambda: {})
    monkeypatch.setattr(conversation, "write_cache", writes.append)

    conversation.add_turn(
        "What is Python?",
        "Python is a programming language.",
        user_metadata={"intent": "chat"},
        assistant_metadata={"intent": "chat", "status": "success"},
    )

    assert len(writes) == 1
    history = writes[0][conversation.KEY]
    assert [message["role"] for message in history] == ["user", "assistant"]
    assert history[0]["metadata"]["intent"] == "chat"


def test_add_turn_skips_action_intent_without_cache_write(monkeypatch):
    conversation = _import_conversation(monkeypatch)
    writes = []

    def fail_read_cache():
        raise AssertionError("command turns should not read/write cache")

    monkeypatch.setattr(conversation, "read_cache", fail_read_cache)
    monkeypatch.setattr(conversation, "write_cache", writes.append)

    conversation.add_turn(
        "Open Chrome",
        "Opening Chrome.",
        user_metadata={"intent": "open_app"},
        assistant_metadata={"intent": "open_app", "status": "success"},
    )

    assert writes == []


def test_add_turn_allows_explicit_conversation_kind(monkeypatch):
    conversation = _import_conversation(monkeypatch)
    writes = []

    monkeypatch.setattr(conversation, "read_cache", lambda: {})
    monkeypatch.setattr(conversation, "write_cache", writes.append)

    conversation.add_turn(
        "Tell me something interesting.",
        "Here is something interesting.",
        user_metadata={"intent": "custom_smalltalk", "kind": "conversation"},
        assistant_metadata={"status": "success"},
    )

    assert len(writes) == 1
