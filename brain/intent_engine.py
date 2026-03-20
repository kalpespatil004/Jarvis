"""
Intent Engine
-------------
Converts raw user text into structured intent data.

Design goals:
- Rule-based (fast, offline, predictable)
- Phrase-aware (avoid keyword traps like "time")
- Extensible (easy to add new intents)
"""
import re
from typing import Dict


def detect_intent(text: str) -> Dict:

    if not text or not text.strip():
        return _unknown_intent()

    text = text.lower().strip()

    # =========================
    # EXIT
    # =========================
    if text in ("exit", "quit", "shutdown", "bye"):
        return {
            "intent": "exit",
            "confidence": 1.0
        }
    
    # =========================
    # SAVE NAME
    # =========================
    import re

    if "my name is" in text:
        match = re.search(r"my name is ([a-zA-Z ]+)", text)

        if match:
            name = match.group(1).strip()

            return {
                "intent": "save_name",
                "name": name,
                "confidence": 0.95
            }

    # =========================
    # ALTERNATIVE (I AM ...)
    # =========================
    if text.startswith("i am"):
        name = text.replace("i am", "").strip()

        return {
            "intent": "save_name",
            "name": name,
            "confidence": 0.9
        }

    # =========================
    # GET NAME
    # =========================
    if "my name" in text:
        return {
            "intent": "get_name",
            "confidence": 0.9
        }
    # =========================
    # OPEN APPS (STRICT)
    # =========================
    if text.startswith("open"):
        parts = text.split()

        if len(parts) >= 2:
            app_name = " ".join(parts[1:])  # take full phrase

            return {
                "intent": "open_app",
                "app": app_name,
                "confidence": 0.95
            }

    # =========================
    # PLAY MUSIC
    # =========================
    if text in ("play music",):
        return {
            "intent": "play_music",
            "confidence": 0.95
        }

    # =========================
    # STOP MUSIC
    # =========================
    if text in ("stop music",):
        return {
            "intent": "stop_music",
            "confidence": 0.95
        }

    # =========================
    # TIME
    # =========================
    if text in ("what time is it",):
        return {
            "intent": "get_time",
            "confidence": 0.95
        }

    # =========================
    # UNKNOWN
    # =========================
    return _unknown_intent()


def _unknown_intent() -> Dict:
    return {
        "intent": "unknown",
        "confidence": 0.0
    }

if __name__ == "__main__":
    test_phrases = [
        "Open Chrome",
        "open youtube",
        "Play music",
        "stop music",
        "What time is it",
        "exit",
        "open notepad"
    ]

    for phrase in test_phrases:
        intent = detect_intent(phrase)
        print(f"Input: '{phrase}' -> Intent: {intent}")