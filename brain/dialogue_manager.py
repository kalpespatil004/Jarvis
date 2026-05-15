"""Dialogue state and policy layer for Jarvis commands.

The dialogue manager sits between NLU and execution.  It turns the flat NLU
payload into a structured command object, asks follow-up questions for missing
required slots, and requests confirmation before risky actions execute.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from brain.nlu.schema import REQUIRED_SLOTS
from system.laptop.app_launcher import canonicalize_app_name

DialogueAction = Literal["execute", "follow_up", "cancelled"]


@dataclass(slots=True)
class DialogueResult:
    action: DialogueAction
    response: str | None = None
    command: dict[str, Any] | None = None
    follow_up: dict[str, Any] | None = None


_SLOT_QUESTIONS: dict[str, str] = {
    "app": "Which app should I open?",
    "level": "What level should I set it to?",
    "word": "Which word should I look up?",
    "name": "What should I use for the name?",
    "pid": "Which process ID should I use?",
    "file": "Which file should I use?",
    "command": "What command should I run?",
    "city": "Which city should I use?",
    "query": "What should I search for?",
    "video": "What should I play on YouTube?",
    "destination": "What destination should I use?",
    "target_price": "What target price should I use?",
}

_RISKY_INTENTS = {"delete", "kill_process", "kill_pid", "close"}
_RISKY_ACTIONS = {
    ("file_manager", "delete"),
    ("process_manager", "kill"),
    ("window_control", "close"),
}
_CONFIRM_YES = re.compile(r"^(yes|yep|yeah|confirm|confirmed|do it|proceed|go ahead|sure|ok|okay)$")
_CONFIRM_NO = re.compile(r"^(no|nope|cancel|stop|abort|don'?t|do not|never mind)$")
_GENERIC_STOPWORDS = {
    "the",
    "a",
    "an",
    "please",
    "for",
    "me",
    "my",
    "it",
    "to",
    "at",
    "on",
}


class DialogueManager:
    """Validates commands and maintains pending dialogue state in context."""

    def handle(self, intent_data: dict[str, Any], context: Any) -> DialogueResult:
        raw_text = (intent_data.get("text") or "").strip()
        normalized = (intent_data.get("normalized_text") or self._normalize(raw_text)).strip()

        confirmation_result = self._handle_pending_confirmation(normalized, context)
        if confirmation_result is not None:
            return confirmation_result

        if context.pending_intent:
            merged = self._merge_pending_intent(intent_data, raw_text, normalized, context)
            if merged is not None:
                intent_data = merged

        intent = intent_data.get("intent", "unknown")
        slots = self._slots_from_intent_data(intent_data)
        missing = self._missing_required_slots(intent, slots)
        if missing:
            return self._ask_for_missing_slot(intent, slots, missing, intent_data, context)

        command = self._structured_command(intent_data, slots)
        if self._requires_confirmation(command):
            context.set_pending_confirmation(command)
            question = self._confirmation_question(command)
            return DialogueResult(
                action="follow_up",
                response=question,
                follow_up={
                    "type": "confirmation",
                    "intent": command["intent"],
                    "question": question,
                    "risky": True,
                },
            )

        context.clear_pending_intent()
        return DialogueResult(action="execute", command=command)

    def _handle_pending_confirmation(self, normalized: str, context: Any) -> DialogueResult | None:
        pending = context.pending_confirmation
        if not pending:
            return None
        if _CONFIRM_YES.match(normalized):
            context.clear_pending_confirmation()
            context.clear_pending_intent()
            return DialogueResult(action="execute", command=pending)
        if _CONFIRM_NO.match(normalized):
            intent = pending.get("intent", "that action")
            context.clear_pending_confirmation()
            context.clear_pending_intent()
            return DialogueResult(action="cancelled", response=f"Cancelled {intent}.")
        question = self._confirmation_question(pending)
        return DialogueResult(
            action="follow_up",
            response=question,
            follow_up={
                "type": "confirmation",
                "intent": pending.get("intent"),
                "question": question,
                "risky": True,
            },
        )

    def _merge_pending_intent(
        self,
        intent_data: dict[str, Any],
        raw_text: str,
        normalized: str,
        context: Any,
    ) -> dict[str, Any] | None:
        pending_intent = context.pending_intent
        missing_slots = list(context.pending_missing_slots)
        pending_slots = dict(context.pending_slots)
        if not pending_intent or not missing_slots:
            return None

        filled = self._infer_slots_from_followup(pending_intent, missing_slots, raw_text, normalized)
        if not filled:
            return None

        pending_slots.update(filled)
        merged = {
            **context.pending_intent_data,
            **intent_data,
            "intent": pending_intent,
            "text": raw_text or context.pending_intent_data.get("text", ""),
            "normalized_text": normalized or context.pending_intent_data.get("normalized_text", ""),
            "confidence": max(float(context.pending_intent_data.get("confidence", 0.0)), 0.9),
        }
        merged.update(pending_slots)
        return merged

    def _ask_for_missing_slot(
        self,
        intent: str,
        slots: dict[str, Any],
        missing: list[str],
        intent_data: dict[str, Any],
        context: Any,
    ) -> DialogueResult:
        slot = missing[0]
        question = _SLOT_QUESTIONS.get(slot, f"Please provide {slot}.")
        context.set_pending_intent(
            intent=intent,
            missing_slots=missing,
            slots=slots,
            intent_data=intent_data,
        )
        follow_up = {
            "type": "slot_request",
            "intent": intent,
            "missing_slots": missing,
            "slot": slot,
            "question": question,
        }
        return DialogueResult(action="follow_up", response=question, follow_up=follow_up)

    def _slots_from_intent_data(self, intent_data: dict[str, Any]) -> dict[str, Any]:
        if isinstance(intent_data.get("slots"), dict):
            return dict(intent_data["slots"])
        reserved = {
            "intent",
            "text",
            "normalized_text",
            "confidence",
            "source",
            "model_confidence",
            "disambiguation_needed",
            "response",
        }
        return {k: v for k, v in intent_data.items() if k not in reserved}

    def _missing_required_slots(self, intent: str, slots: dict[str, Any]) -> list[str]:
        required = list(REQUIRED_SLOTS.get(intent, ()))
        action = slots.get("action")
        if intent == "file_manager":
            if action in {"create_folder", "delete", "move", "copy"}:
                required.append("name")
            if action in {"move", "copy"}:
                required.append("destination")
        elif intent == "process_manager" and action == "kill":
            required.append("name")
        elif intent == "window_control" and action == "focus":
            required.append("name")
        seen: set[str] = set()
        missing: list[str] = []
        for slot in required:
            if slot not in seen and self._is_missing(slots.get(slot)):
                missing.append(slot)
            seen.add(slot)
        return missing

    def _structured_command(self, intent_data: dict[str, Any], slots: dict[str, Any]) -> dict[str, Any]:
        intent = intent_data.get("intent", "unknown")
        return {
            "type": "command",
            "intent": intent,
            "slots": slots,
            "text": intent_data.get("text", ""),
            "metadata": {
                "confidence": intent_data.get("confidence", 0.0),
                "source": intent_data.get("source", "unknown"),
                "model_confidence": intent_data.get("model_confidence", intent_data.get("confidence", 0.0)),
                "disambiguation_needed": intent_data.get("disambiguation_needed", False),
                "response": intent_data.get("response"),
                "normalized_text": intent_data.get("normalized_text", ""),
            },
        }

    def _requires_confirmation(self, command: dict[str, Any]) -> bool:
        intent = command.get("intent")
        slots = command.get("slots", {})
        return intent in _RISKY_INTENTS or (intent, slots.get("action")) in _RISKY_ACTIONS

    def _confirmation_question(self, command: dict[str, Any]) -> str:
        intent = command.get("intent", "this action")
        slots = command.get("slots", {})
        target = slots.get("name") or slots.get("pid") or slots.get("app") or slots.get("file")
        if intent == "close" or (intent, slots.get("action")) == ("window_control", "close"):
            return "Closing a window can lose unsaved work. Should I close it?"
        if intent in {"kill_process", "kill_pid"} or (intent, slots.get("action")) == ("process_manager", "kill"):
            suffix = f" '{target}'" if target else ""
            return f"Killing process{suffix} may cause data loss. Should I proceed?"
        if intent == "delete" or (intent, slots.get("action")) == ("file_manager", "delete"):
            suffix = f" '{target}'" if target else ""
            return f"Deleting{suffix} may be permanent. Should I proceed?"
        return f"This is a risky action ({intent}). Should I proceed?"

    def _infer_slots_from_followup(
        self,
        intent: str,
        missing_slots: list[str],
        raw_text: str,
        normalized: str,
    ) -> dict[str, Any]:
        filled: dict[str, Any] = {}
        for slot in missing_slots:
            value = self._infer_slot_value(intent, slot, raw_text, normalized)
            if not self._is_missing(value):
                filled[slot] = value
        return filled

    def _infer_slot_value(self, intent: str, slot: str, raw_text: str, normalized: str) -> Any:
        if slot == "app":
            cleaned = re.sub(r"\b(open|launch|start|run|app|application|please)\b", "", normalized).strip()
            return canonicalize_app_name(cleaned or raw_text)
        if slot == "level":
            if re.search(r"\b(max|full|maximum)\b", normalized):
                return 100
            if re.search(r"\b(min|mute|zero|silent)\b", normalized):
                return 0
            m = re.search(r"(\d{1,3})", normalized)
            if m:
                return max(0, min(100, int(m.group(1))))
            return None
        if slot == "pid":
            m = re.search(r"\d+", normalized)
            return int(m.group(0)) if m else None
        if slot == "target_price":
            m = re.search(r"\d+(?:\.\d+)?", normalized)
            return float(m.group(0)) if m else None
        if slot in {"name", "file", "word", "city", "query", "video", "command", "destination"}:
            return self._clean_free_text(normalized if normalized else raw_text)
        return self._clean_free_text(raw_text)

    @staticmethod
    def _clean_free_text(text: str) -> str:
        cleaned = " ".join(token for token in text.split() if token not in _GENERIC_STOPWORDS)
        return cleaned.strip()

    @staticmethod
    def _is_missing(value: Any) -> bool:
        return value is None or value == "" or value == [] or value == {}

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text)


dialogue_manager = DialogueManager()
