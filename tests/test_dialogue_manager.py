import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain.context import ContextManager
from brain.dialogue_manager import DialogueManager


def test_missing_required_slot_returns_structured_follow_up():
    ctx = ContextManager()
    manager = DialogueManager()

    result = manager.handle(
        {
            "intent": "open_app",
            "text": "open an app",
            "normalized_text": "open an app",
            "confidence": 0.8,
        },
        ctx,
    )

    assert result.action == "follow_up"
    assert result.response == "Which app should I open?"
    assert result.follow_up == {
        "type": "slot_request",
        "intent": "open_app",
        "missing_slots": ["app"],
        "slot": "app",
        "question": "Which app should I open?",
    }
    assert ctx.pending_intent == "open_app"
    assert ctx.pending_missing_slots == ["app"]


def test_pending_slot_answer_builds_structured_command():
    ctx = ContextManager()
    manager = DialogueManager()
    manager.handle(
        {
            "intent": "open_app",
            "text": "open an app",
            "normalized_text": "open an app",
            "confidence": 0.8,
        },
        ctx,
    )

    result = manager.handle(
        {
            "intent": "chat",
            "text": "Chrome",
            "normalized_text": "chrome",
            "confidence": 0.4,
        },
        ctx,
    )

    assert result.action == "execute"
    assert result.command["type"] == "command"
    assert result.command["intent"] == "open_app"
    assert result.command["slots"] == {"app": "chrome"}
    assert ctx.pending_intent is None


def test_risky_action_requires_confirmation_before_execution():
    ctx = ContextManager()
    manager = DialogueManager()

    result = manager.handle(
        {
            "intent": "delete",
            "text": "delete notes.txt",
            "normalized_text": "delete notes txt",
            "confidence": 0.9,
            "name": "notes.txt",
        },
        ctx,
    )

    assert result.action == "follow_up"
    assert result.follow_up["type"] == "confirmation"
    assert ctx.pending_confirmation["intent"] == "delete"

    confirmed = manager.handle(
        {
            "intent": "chat",
            "text": "yes",
            "normalized_text": "yes",
            "confidence": 0.4,
        },
        ctx,
    )

    assert confirmed.action == "execute"
    assert confirmed.command["intent"] == "delete"
    assert confirmed.command["slots"] == {"name": "notes.txt"}
    assert ctx.pending_confirmation is None
