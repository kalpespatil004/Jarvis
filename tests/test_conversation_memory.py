import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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


def test_add_turn_persists_chat_intent_to_conversation_turns(monkeypatch):
    conversation = _import_conversation(monkeypatch)
    writes = []
    pushed = []

    monkeypatch.setattr(conversation, "read_cache", lambda: {})
    monkeypatch.setattr(conversation, "write_cache", writes.append)
    monkeypatch.setattr(conversation, "push_conversation_turn", pushed.append)

    conversation.add_turn(
        "What is Python?",
        "Python is a programming language.",
        user_metadata={"intent": "chat"},
        assistant_metadata={"intent": "chat", "status": "success"},
    )

    assert len(writes) == 1
    turns = writes[0][conversation.CONVERSATION_TURNS_KEY]
    assert len(turns) == 1
    assert turns[0]["user_text"] == "What is Python?"
    assert turns[0]["assistant_text"] == "Python is a programming language."
    assert turns[0]["metadata"]["user"]["intent"] == "chat"
    assert turns[0]["metadata"]["assistant"]["status"] == "success"
    assert pushed == [turns[0]]

    # Legacy history remains available for callers that still depend on raw messages.
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
    monkeypatch.setattr(conversation, "push_conversation_turn", lambda turn: None)

    conversation.add_turn(
        "Tell me something interesting.",
        "Here is something interesting.",
        user_metadata={"intent": "custom_smalltalk", "kind": "conversation"},
        assistant_metadata={"status": "success"},
    )

    assert len(writes) == 1
    assert writes[0][conversation.CONVERSATION_TURNS_KEY][0]["user_text"] == "Tell me something interesting."


def test_add_turn_trims_conversation_turns_to_newest_20(monkeypatch):
    conversation = _import_conversation(monkeypatch)
    writes = []
    existing_turns = [
        {"user_text": f"u{i}", "assistant_text": f"a{i}", "time": str(i), "metadata": {}}
        for i in range(20)
    ]

    monkeypatch.setattr(
        conversation,
        "read_cache",
        lambda: {conversation.CONVERSATION_TURNS_KEY: list(existing_turns), conversation.KEY: []},
    )
    monkeypatch.setattr(conversation, "write_cache", writes.append)
    monkeypatch.setattr(conversation, "push_conversation_turn", lambda turn: None)

    conversation.add_turn(
        "new user",
        "new assistant",
        user_metadata={"intent": "chat"},
        assistant_metadata={"intent": "chat"},
    )

    turns = writes[0][conversation.CONVERSATION_TURNS_KEY]
    assert len(turns) == 20
    assert turns[0]["user_text"] == "u1"
    assert turns[-1]["user_text"] == "new user"


def test_get_recent_turns_reads_conversation_turns_not_legacy_history(monkeypatch):
    conversation = _import_conversation(monkeypatch)
    data = {
        conversation.CONVERSATION_TURNS_KEY: [
            {"user_text": "first", "assistant_text": "one", "time": "1", "metadata": {}},
            {"user_text": "second", "assistant_text": "two", "time": "2", "metadata": {}},
        ],
        conversation.KEY: [
            {"role": "user", "text": "legacy", "time": "0", "metadata": {"intent": "chat"}},
            {"role": "assistant", "text": "old", "time": "0", "metadata": {"intent": "chat"}},
        ],
    }
    monkeypatch.setattr(conversation, "read_cache", lambda: data)

    assert conversation.get_recent_turns(1) == [data[conversation.CONVERSATION_TURNS_KEY][1]]


def test_get_recent_turns_migrates_legacy_history_without_action_turns(monkeypatch):
    conversation = _import_conversation(monkeypatch)
    data = {
        conversation.KEY: [
            {"role": "user", "text": "hello", "time": "1", "metadata": {"intent": "greeting"}},
            {"role": "assistant", "text": "hi", "time": "1", "metadata": {"intent": "greeting"}},
            {"role": "user", "text": "open chrome", "time": "2", "metadata": {"intent": "open_app"}},
            {"role": "assistant", "text": "opening", "time": "2", "metadata": {"intent": "open_app"}},
        ]
    }
    monkeypatch.setattr(conversation, "read_cache", lambda: data)

    assert conversation.get_recent_turns() == [
        {
            "user_text": "hello",
            "assistant_text": "hi",
            "time": "1",
            "metadata": {
                "user": {"intent": "greeting"},
                "assistant": {"intent": "greeting"},
            },
        }
    ]
