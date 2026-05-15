#!/usr/bin/env python3
"""Offline dialogue scenario evaluator for Jarvis NLU follow-up behavior.

The evaluator intentionally stops at intent/dialogue resolution. It never routes
commands to OS services, never speaks, and replaces the LLM fallback with a
local deterministic chat response so CI can run offline.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain.context import context  # noqa: E402
from brain.dialogue_manager import DialogueResult, dialogue_manager  # noqa: E402
from brain.intent_engine import detect_intent  # noqa: E402
import brain.intent_engine as intent_engine  # noqa: E402

SCENARIO_DIR = Path(__file__).resolve().parent
DEFAULT_THRESHOLDS = {
    "intent_accuracy": 1.0,
    "slot_fill_accuracy": 1.0,
    "context_carryover_success": 1.0,
    "clarification_appropriateness": 1.0,
}


@dataclass
class Counter:
    passed: int = 0
    total: int = 0

    def add(self, ok: bool) -> None:
        self.total += 1
        if ok:
            self.passed += 1

    @property
    def ratio(self) -> float:
        return 1.0 if self.total == 0 else self.passed / self.total


@dataclass
class Evaluation:
    intent_accuracy: Counter = field(default_factory=Counter)
    slot_fill_accuracy: Counter = field(default_factory=Counter)
    context_carryover_success: Counter = field(default_factory=Counter)
    clarification_appropriateness: Counter = field(default_factory=Counter)
    failures: list[str] = field(default_factory=list)

    def as_metrics(self) -> dict[str, float]:
        return {
            "intent_accuracy": self.intent_accuracy.ratio,
            "slot_fill_accuracy": self.slot_fill_accuracy.ratio,
            "context_carryover_success": self.context_carryover_success.ratio,
            "clarification_appropriateness": self.clarification_appropriateness.ratio,
        }


def _reset_context() -> None:
    context.__init__()  # reset the shared global ContextManager in-place
    dialogue_manager.__init__()


def _install_offline_llm_stub() -> None:
    intent_engine.llm_chat = lambda _prompt: '{"intent":"chat","parameters":{}}'


def _slot_value(payload: dict[str, Any], key: str) -> Any:
    if isinstance(payload.get("slots"), dict) and key in payload["slots"]:
        return payload["slots"][key]
    return payload.get(key)


def _values_equal(actual: Any, expected: Any) -> bool:
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        return abs(float(actual) - expected) < 0.000001
    return actual == expected


def _memory_context(recent_turns: list[dict[str, Any]]) -> dict[str, Any]:
    return {"recent_turns": recent_turns[-6:]}


def _remember_turn(recent_turns: list[dict[str, Any]], user: str, intent_data: dict[str, Any], dialogue: DialogueResult) -> None:
    assistant_text = dialogue.response or ""
    if dialogue.command:
        assistant_text = f"execute:{dialogue.command.get('intent')}"
    recent_turns.append(
        {
            "user": {"text": user, "metadata": dict(intent_data)},
            "assistant": {
                "text": assistant_text,
                "metadata": {"status": dialogue.action, "intent": intent_data.get("intent")},
            },
        }
    )


def _context_carried(intent_data: dict[str, Any], dialogue: DialogueResult, expected: dict[str, Any]) -> bool:
    if intent_data.get("source") == "context_followup":
        return True
    if intent_data.get("temporal_followup") is True:
        return True
    if expected.get("dialogue", {}).get("command_intent") and dialogue.command:
        return dialogue.command.get("intent") == expected["dialogue"]["command_intent"]
    return False


def _check_dialogue(
    scenario_name: str,
    turn_number: int,
    expected_dialogue: dict[str, Any],
    dialogue: DialogueResult,
    evaluation: Evaluation,
) -> None:
    action = expected_dialogue.get("action")
    if action is not None and dialogue.action != action:
        evaluation.failures.append(
            f"{scenario_name} turn {turn_number}: dialogue.action expected {action!r}, got {dialogue.action!r}"
        )

    follow_up_type = expected_dialogue.get("follow_up_type")
    if follow_up_type is not None:
        actual_type = (dialogue.follow_up or {}).get("type")
        if actual_type != follow_up_type:
            evaluation.failures.append(
                f"{scenario_name} turn {turn_number}: follow_up.type expected {follow_up_type!r}, got {actual_type!r}"
            )

    missing_slots = expected_dialogue.get("missing_slots")
    if missing_slots is not None:
        actual_missing = (dialogue.follow_up or {}).get("missing_slots")
        if actual_missing != missing_slots:
            evaluation.failures.append(
                f"{scenario_name} turn {turn_number}: missing_slots expected {missing_slots!r}, got {actual_missing!r}"
            )

    command_intent = expected_dialogue.get("command_intent")
    if command_intent is not None:
        actual_intent = (dialogue.command or {}).get("intent")
        if actual_intent != command_intent:
            evaluation.failures.append(
                f"{scenario_name} turn {turn_number}: command.intent expected {command_intent!r}, got {actual_intent!r}"
            )

    for key, expected_value in expected_dialogue.get("command_slots", {}).items():
        evaluation.slot_fill_accuracy.add(_values_equal((dialogue.command or {}).get("slots", {}).get(key), expected_value))
        if not _values_equal((dialogue.command or {}).get("slots", {}).get(key), expected_value):
            evaluation.failures.append(
                f"{scenario_name} turn {turn_number}: command slot {key!r} expected {expected_value!r}, "
                f"got {(dialogue.command or {}).get('slots', {}).get(key)!r}"
            )


def _check_clarification(
    scenario_name: str,
    turn_number: int,
    expected: str,
    intent_data: dict[str, Any],
    dialogue: DialogueResult,
    evaluation: Evaluation,
) -> None:
    if expected == "ask_slot":
        ok = dialogue.action == "follow_up" and (dialogue.follow_up or {}).get("type") == "slot_request"
    elif expected == "ask_confirmation":
        ok = dialogue.action == "follow_up" and (dialogue.follow_up or {}).get("type") == "confirmation"
    elif expected == "resolved":
        ok = dialogue.action in {"execute", "cancelled"}
    elif expected == "none":
        ok = not intent_data.get("disambiguation_needed") and dialogue.action != "follow_up"
    else:
        ok = False

    evaluation.clarification_appropriateness.add(ok)
    if not ok:
        evaluation.failures.append(
            f"{scenario_name} turn {turn_number}: clarification expected {expected!r}, "
            f"got intent disambiguation={intent_data.get('disambiguation_needed')!r}, dialogue={dialogue.action!r}"
        )


def evaluate_scenario(path: Path, evaluation: Evaluation) -> None:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    scenario_name = scenario.get("name", path.stem)
    recent_turns: list[dict[str, Any]] = []
    _reset_context()

    for turn_number, turn in enumerate(scenario.get("turns", []), start=1):
        user = turn["user"]
        expected = turn.get("expect", {})
        intent_data = detect_intent(user, memory_context=_memory_context(recent_turns))

        expected_intent = expected.get("intent")
        if expected_intent is not None:
            ok = intent_data.get("intent") == expected_intent
            evaluation.intent_accuracy.add(ok)
            if not ok:
                evaluation.failures.append(
                    f"{scenario_name} turn {turn_number}: intent expected {expected_intent!r}, got {intent_data.get('intent')!r}"
                )

        for key, expected_value in expected.get("slots", {}).items():
            actual_value = _slot_value(intent_data, key)
            ok = _values_equal(actual_value, expected_value)
            evaluation.slot_fill_accuracy.add(ok)
            if not ok:
                evaluation.failures.append(
                    f"{scenario_name} turn {turn_number}: slot {key!r} expected {expected_value!r}, got {actual_value!r}"
                )

        expected_source = expected.get("source")
        if expected_source is not None and intent_data.get("source") != expected_source:
            evaluation.failures.append(
                f"{scenario_name} turn {turn_number}: source expected {expected_source!r}, got {intent_data.get('source')!r}"
            )

        context.update(intent_data)
        dialogue = dialogue_manager.handle(intent_data, context)

        if "dialogue" in expected:
            _check_dialogue(scenario_name, turn_number, expected["dialogue"], dialogue, evaluation)

        if expected.get("context_carryover") is True:
            ok = _context_carried(intent_data, dialogue, expected)
            evaluation.context_carryover_success.add(ok)
            if not ok:
                evaluation.failures.append(f"{scenario_name} turn {turn_number}: expected context carry-over resolution")

        if "clarification" in expected:
            _check_clarification(scenario_name, turn_number, expected["clarification"], intent_data, dialogue, evaluation)

        _remember_turn(recent_turns, user, intent_data, dialogue)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate dialogue follow-up scenarios offline.")
    parser.add_argument("paths", nargs="*", type=Path, help="Scenario JSON files. Defaults to tests/dialogue/*.json")
    parser.add_argument("--json", action="store_true", help="Print machine-readable metrics JSON")
    args = parser.parse_args()

    _install_offline_llm_stub()
    paths = args.paths or sorted(SCENARIO_DIR.glob("*.json"))
    evaluation = Evaluation()
    for path in paths:
        evaluate_scenario(path, evaluation)

    metrics = evaluation.as_metrics()
    failed_thresholds = [name for name, threshold in DEFAULT_THRESHOLDS.items() if metrics[name] < threshold]

    if args.json:
        print(json.dumps({"metrics": metrics, "failures": evaluation.failures}, indent=2, sort_keys=True))
    else:
        print("Dialogue scenario metrics:")
        for name, value in metrics.items():
            print(f"  {name}: {value:.2%}")
        if evaluation.failures:
            print("\nFailures:")
            for failure in evaluation.failures:
                print(f"  - {failure}")

    return 1 if evaluation.failures or failed_thresholds else 0


if __name__ == "__main__":
    raise SystemExit(main())
