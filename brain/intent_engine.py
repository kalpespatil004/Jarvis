"""
Intent Engine
-------------
Converts raw user text into structured intent data.

Design goals:
- Rule-based NLP (fast, offline, predictable)
- Phrase-aware matching (avoid weak keyword traps)
- Extensible entity extraction for routing/services
"""

from __future__ import annotations

import re
from typing import Any

_APP_ALIASES = {
    "google chrome": "chrome",
    "chrome browser": "chrome",
    "microsoft edge": "edge",
    "edge browser": "edge",
    "calculator": "calculator",
    "calc": "calculator",
    "notepad": "notepad",
}

_APP_STOPWORDS = {
    "app",
    "application",
    "named",
    "please",
    "for",
    "me",
    "the",
    "a",
    "an",
    "to",
    "jarvis",
}


def detect_intent(text: str) -> dict[str, Any]:
    """Detect intent and lightweight entities from a user utterance."""
    if not text or not text.strip():
        return _unknown_intent()

    raw_text = text.strip()
    normalized = _normalize(raw_text)

    if re.fullmatch(r"(?:exit|quit|shutdown|bye|goodbye|close jarvis)", normalized):
        return _intent("exit", raw_text, normalized, confidence=1.0)

    if re.search(r"\b(best time|good time|ideal time|when should i)\b", normalized):
        return _intent("advice_time", raw_text, normalized, confidence=0.84, topic=raw_text)

    if re.search(
        r"\b(what\s+time\s+is\s+it|tell\s+me\s+the\s+time|current\s+time|time\s+now)\b",
        normalized,
    ):
        return _intent("get_time", raw_text, normalized, confidence=0.96)

    if re.search(
        r"\b(what\s+date\s+is\s+it|today'?s\s+date|current\s+date|date\s+today)\b",
        normalized,
    ):
        return _intent("get_date", raw_text, normalized, confidence=0.96)

    app_name = _extract_app_name(normalized)
    if app_name:
        return _intent("open_app", raw_text, normalized, confidence=0.90, app=app_name)

    if re.search(r"\b(play|start|resume)\b.*\b(music|song|songs|playlist)\b", normalized):
        return _intent("play_music", raw_text, normalized, confidence=0.91)

    if re.search(r"\b(stop|pause)\b.*\b(music|song|songs|playlist)\b", normalized):
        return _intent("stop_music", raw_text, normalized, confidence=0.91)

    return _intent("chat", raw_text, normalized, confidence=0.45, text=raw_text)


def _normalize(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def _extract_app_name(text: str) -> str | None:
    explicit_patterns = [
        r"\bopen\s+(.+)$",
        r"\blaunch\s+(.+)$",
        r"\bstart\s+(.+)$",
        r"\brun\s+(.+)$",
    ]

    candidate: str | None = None
    for pattern in explicit_patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            break

    if not candidate:
        return None

    tokens = [token for token in candidate.split() if token not in _APP_STOPWORDS]
    if not tokens:
        return None

    cleaned = " ".join(tokens[:3]).strip()
    return _APP_ALIASES.get(cleaned, cleaned)


def _intent(intent: str, raw_text: str, normalized_text: str, confidence: float, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "intent": intent,
        "text": raw_text,
        "normalized_text": normalized_text,
        "confidence": confidence,
    }
    payload.update(extra)
    return payload


def _unknown_intent() -> dict[str, Any]:
    return {
        "intent": "unknown",
        "text": "",
        "normalized_text": "",
        "confidence": 0.0,
    }
