from __future__ import annotations

import re
from typing import Any

from brain.context import context
from services.time_date.temporal_reasoner import TEMPORAL_REASONER

_ANAPHORA_RE = re.compile(r"\b(it|that|same|there)\b")


class FollowupResolver:
    """Resolve anaphora/ellipsis by reusing recent context frames."""

    def resolve_slots(
        self,
        raw_text: str,
        normalized: str,
        intent: str,
        slots: dict[str, Any],
        required_slots: tuple[str, ...],
        memory_context: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        meta: dict[str, Any] = {"resolved": False, "ambiguity": None}
        if not required_slots:
            return slots, meta

        missing = [k for k in required_slots if not slots.get(k)]
        if not missing:
            return slots, meta

        needs_context = bool(_ANAPHORA_RE.search(normalized)) or self._looks_elliptical(normalized)
        if not needs_context:
            return slots, meta

        candidates = self._candidate_frames(intent, missing, memory_context or {})
        if not candidates:
            return slots, meta
        if len(candidates) > 1:
            labels = self._candidate_labels(candidates)
            if len(labels) > 1:
                meta["ambiguity"] = f"Do you mean {labels[0]} or {labels[1]}?"
                return slots, meta

        best = candidates[0]
        merged = dict(slots)
        for key in missing:
            value = best.get(key)
            if value is not None:
                merged[key] = value
                meta["resolved"] = True
        return merged, meta

    def resolve_temporal_followup(self, raw_text: str, normalized: str, last_intent: str | None) -> dict[str, Any] | None:
        resolution = TEMPORAL_REASONER.resolve_followup(
            raw_text,
            last_intent=last_intent,
            last_date_ref=context.get_last_date_ref(),
        )
        if resolution is None:
            return None
        return {"intent": "get_date", **resolution.as_slots()}

    @staticmethod
    def _looks_elliptical(normalized: str) -> bool:
        return bool(
            re.match(r"^(set\s+\d{1,3}%|set\s+to\s+\d{1,3}%|maximize\s+it|tell\s+me\s+tomorrow\s*s?|what\s+about\s+next\s+week|tomorrow\s*s?)$", normalized)
        )

    @staticmethod
    def _candidate_labels(candidates: list[dict[str, Any]]) -> list[str]:
        labels: list[str] = []
        for frame in candidates[:2]:
            if frame.get("app"):
                labels.append(f"{frame['app']} window")
            elif frame.get("name"):
                labels.append(f"{frame['name']} window")
            elif frame.get("city"):
                labels.append(f"weather in {frame['city']}")
            else:
                labels.append(frame.get("intent", "that one"))
        return labels

    @staticmethod
    def _candidate_frames(intent: str, missing: list[str], memory_context: dict[str, Any]) -> list[dict[str, Any]]:
        frames = []
        seen: set[tuple[str, str]] = set()

        def add_frame(frame: dict[str, Any]):
            key = (str(frame.get("intent", "")), str(frame.get("text", "")))

            if key in seen:
                return

            if all(frame.get(k) for k in missing):
                frames.append(frame)
                seen.add(key)

        for frame in reversed(context.get_history()):
            add_frame(frame)
            if len(frames) == 3:
                return frames

        for turn in reversed(memory_context.get("recent_turns", []) or []):
            if not isinstance(turn, dict):
                continue

            # New memory turns are stored as {user_text, assistant_text, time, metadata}
            # with user metadata nested under metadata.user. Accept the legacy
            # {user, assistant} shape as a compatibility fallback.
            turn_metadata = turn.get("metadata") if isinstance(turn.get("metadata"), dict) else {}
            metadata = turn_metadata.get("user") if isinstance(turn_metadata.get("user"), dict) else None
            user_text = turn.get("user_text", "")
            if metadata is None:
                user_msg = turn.get("user") or {}
                metadata = user_msg.get("metadata") if isinstance(user_msg, dict) else {}
                user_text = user_msg.get("text", "") if isinstance(user_msg, dict) else ""

            if isinstance(metadata, dict):
                frame = dict(metadata)
                frame.setdefault("text", user_text)
                add_frame(frame)
            if len(frames) == 3:
                break
        return frames


FOLLOWUP_RESOLVER = FollowupResolver()
