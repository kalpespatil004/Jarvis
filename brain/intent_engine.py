from __future__ import annotations

import re
import json
from typing import Any

from LLM.offlineLLM import chat as llm_chat


# =========================
# AVAILABLE INTENTS (FOR LLM)
# =========================
AVAILABLE_INTENTS = [
    "exit", "greeting", "advice_time",
    "get_time", "get_date",
    "open_app",
    "play_music", "stop_music",
    "brightness_control",
    "volume_control",
    "file_manager",
    "process_manager",
    "window_control",
    "screenshot",
    "run_code"
]


# =========================
# MAIN DETECTOR
# =========================
def detect_intent(text: str) -> dict[str, Any]:

    if not text or not text.strip():
        return _unknown_intent()

    raw_text = text.strip()
    normalized = _normalize(raw_text)

    # =========================
    # EXIT INTENT
    # User wants to stop Jarvis
    # =========================
    if re.fullmatch(r"(?:exit|quit|shutdown|bye|goodbye|close jarvis)", normalized):
        return _intent("exit", raw_text, normalized, 1.0)

    # =========================
    # GREETING INTENT
    # Simple hello/hi
    # =========================
    if re.fullmatch(r"(?:hey|hi|hello|hey jarvis|hi jarvis|hello jarvis)", normalized):
        return _intent("greeting", raw_text, normalized, 0.98)

    # =========================
    # ADVICE TIME
    # User asking best time for something
    # =========================
    if re.search(r"\b(best time|good time|ideal time|when should i)\b", normalized):
        return _intent("advice_time", raw_text, normalized, 0.84, topic=raw_text)

    # =========================
    # TIME QUERY
    # =========================
    if re.search(r"\b(what\s+time\s+is\s+it|tell\s+me\s+the\s+time|current\s+time|time\s+now)\b", normalized):
        return _intent("get_time", raw_text, normalized, 0.96)

    # =========================
    # DATE QUERY
    # =========================
    if re.search(r"\b(what\s+date\s+is\s+it|today'?s\s+date|current\s+date|date\s+today)\b", normalized):
        return _intent("get_date", raw_text, normalized, 0.96)

    # =========================
    # OPEN APP
    # =========================
    app_name = _extract_app_name(normalized)
    if app_name:
        return _intent("open_app", raw_text, normalized, 0.90, app=app_name)

    # =========================
    # MUSIC CONTROL
    # =========================
    if re.search(r"\b(play|start|resume)\b.*\b(music|song|songs|playlist)\b", normalized):
        return _intent("play_music", raw_text, normalized, 0.91)

    if re.search(r"\b(stop|pause)\b.*\b(music|song|songs|playlist)\b", normalized):
        return _intent("stop_music", raw_text, normalized, 0.91)

    # =========================
    # BRIGHTNESS CONTROL
    # =========================
    if "brightness" in normalized:
        if "max" in normalized:
            return _intent("brightness_control", raw_text, normalized, 0.95, level=100)
        if "min" in normalized:
            return _intent("brightness_control", raw_text, normalized, 0.95, level=0)

        match = re.search(r"(\d+)", normalized)
        if match:
            return _intent("brightness_control", raw_text, normalized, 0.9, level=int(match.group(1)))

        return _intent("brightness_control", raw_text, normalized, 0.7)

    # =========================
    # VOLUME CONTROL
    # =========================
    if "volume" in normalized:
        match = re.search(r"(\d+)", normalized)
        if match:
            return _intent("volume_control", raw_text, normalized, 0.9, level=int(match.group(1)))

        return _intent("volume_control", raw_text, normalized, 0.7)

    # =========================
    # FILE MANAGEMENT
    # =========================
    if "create folder" in normalized:
        name = normalized.replace("create folder", "").strip()
        return _intent("file_manager", raw_text, normalized, 0.9, action="create_folder", name=name)

    if "delete" in normalized:
        name = normalized.replace("delete", "").strip()
        return _intent("file_manager", raw_text, normalized, 0.85, action="delete", name=name)

    # =========================
    # WINDOW CONTROL
    # =========================
    if "minimize" in normalized:
        return _intent("window_control", raw_text, normalized, 0.9, action="minimize")

    if "maximize" in normalized:
        return _intent("window_control", raw_text, normalized, 0.9, action="maximize")

    # =========================
    # SCREENSHOT
    # =========================
    if "screenshot" in normalized:
        return _intent("screenshot", raw_text, normalized, 0.9)

    # =========================
    # RUN CODE
    # =========================
    if "run python" in normalized:
        file = normalized.replace("run python", "").strip()
        return _intent("run_code", raw_text, normalized, 0.9, file=file)

    # =========================
    # 🤖 LLM FALLBACK (SMART PART)
    # =========================
    return _llm_fallback(raw_text)


# =========================
# LLM INTENT CLASSIFIER
# =========================
def _llm_fallback(text: str) -> dict:

    prompt = f"""
You are an intent classifier.

Available intents:
{AVAILABLE_INTENTS}

Return ONLY valid JSON.

Format:
{{
  "intent": "intent_name",
  "parameters": {{}}
}}

Examples:
User: set brightness to max
Output:
{{"intent": "brightness_control", "parameters": {{"level": 100}}}}

User: open chrome
Output:
{{"intent": "open_app", "parameters": {{"app": "chrome"}}}}

User: {text}
"""

    response = llm_chat(prompt)

    try:
        parsed = json.loads(response)
        return {
            "intent": parsed.get("intent", "chat"),
            **parsed.get("parameters", {})
        }
    except Exception:
        return _intent("chat", text, _normalize(text), 0.3, text=text)


# =========================
# HELPERS
# =========================
def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_app_name(text: str) -> str | None:
    patterns = [r"\bopen\s+(.+)$", r"\blaunch\s+(.+)$", r"\bstart\s+(.+)$", r"\brun\s+(.+)$"]

    for p in patterns:
        match = re.search(p, text)
        if match:
            candidate = match.group(1).strip()
            tokens = [t for t in candidate.split() if t not in _APP_STOPWORDS]
            if tokens:
                return " ".join(tokens[:3])

    return None


def _intent(intent: str, raw: str, norm: str, confidence: float, **extra: Any) -> dict:
    data = {
        "intent": intent,
        "text": raw,
        "normalized_text": norm,
        "confidence": confidence,
    }
    data.update(extra)
    return data


def _unknown_intent() -> dict:
    return {"intent": "unknown", "confidence": 0.0}