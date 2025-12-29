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
    """
    Detect intent from user command.

    Returns:
    {
        "intent": str,
        optional metadata...,
        "confidence": float
    }
    """

    if not text or not text.strip():
        return _unknown_intent()

    text = text.lower().strip()

    # =========================
    # EXIT / SHUTDOWN
    # =========================
    if re.fullmatch(r"(exit|quit|shutdown|bye|goodbye)", text):
        return {
            "intent": "exit",
            "confidence": 1.0
        }

    # =========================
    # ADVICE / BEST TIME (IMPORTANT: BEFORE CLOCK TIME)
    # =========================
    if re.search(r"\b(best time|good time|ideal time)\b", text):
        return {
            "intent": "advice_time",
            "topic": text,
            "confidence": 0.85
        }

    # =========================
    # CURRENT TIME (CLOCK)
    # =========================
    if re.search(
        r"\b(what\s+time\s+is\s+it|tell\s+me\s+the\s+time|current\s+time)\b",
        text
    ):
        return {
            "intent": "get_time",
            "confidence": 0.95
        }

    # =========================
    # CURRENT DATE
    # =========================
    if re.search(
        r"\b(what\s+date\s+is\s+it|today'?s\s+date|current\s+date|today)\b",
        text
    ):
        return {
            "intent": "get_date",
            "confidence": 0.95
        }

    # =========================
    # OPEN APPLICATION (ROBUST)
    # =========================
    if re.search(r"\bopen\b", text):
        # Remove everything before 'open'
        after_open = re.split(r"\bopen\b", text, maxsplit=1)[1]

        # Words to ignore
        ignore_words = {
            "app", "application", "named", "please",
            "for", "me", "the", "a", "an", "to"
        }

        # Tokenize
        words = after_open.strip().split()

        # Pick first meaningful word
        for word in words:
            if word not in ignore_words:
                return {
                    "intent": "open_app",
                    "app": word,
                    "confidence": 0.90
                }


    # =========================
    # PLAY MUSIC
    # =========================
    if re.search(
        r"\b(play\s+music|play\s+song|start\s+music)\b",
        text
    ):
        return {
            "intent": "play_music",
            "confidence": 0.90
        }

    # =========================
    # STOP MUSIC
    # =========================
    if re.search(
        r"\b(stop\s+music|pause\s+music|stop\s+song)\b",
        text
    ):
        return {
            "intent": "stop_music",
            "confidence": 0.90
        }

    # =========================
    # FALLBACK: GENERAL CHAT
    # =========================
    return {
        "intent": "chat",
        "text": text,
        "confidence": 0.40
    }


# =========================
# HELPERS
# =========================
def _unknown_intent() -> Dict:
    return {
        "intent": "unknown",
        "confidence": 0.0
    }


# =========================
# DEBUG / SELF TEST
# =========================
if __name__ == "__main__":
    test_commands = [
        "what time is it",
        "tell me the time",
        "best time for study",
        "good time to sleep",
        "hey jarvis i want to open chrome for browsing",
        "can you open app named notepad please",
        "play music on spotify",
        "stop music",
        "what is today's date",
        "exit",
        "how are you"
        "gjhgjcfghjc hgchbjkchr hcwehfkujf"
    ]

    for cmd in test_commands:
        print(f"{cmd}  ->  {detect_intent(cmd)}")
