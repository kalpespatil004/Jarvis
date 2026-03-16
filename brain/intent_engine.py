"""
Intent Engine
-------------
Converts raw user text into structured intent data.

Design:
- Rule-based (fast, offline, predictable)
- Phrase-aware (avoids keyword traps)
- Covers ALL Jarvis features
- Extensible
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

    # ============================================================
    # EXIT / SHUTDOWN
    # ============================================================
    if re.fullmatch(r"(exit|quit|shutdown|bye|goodbye|power\s*off|turn\s*off)", text):
        return {"intent": "exit", "confidence": 1.0}

    # ============================================================
    # TIME & DATE
    # ============================================================
    if re.search(r"\b(what\s+time\s+is\s+it|tell\s+me\s+the\s+time|current\s+time|time\s+now)\b", text):
        return {"intent": "get_time", "confidence": 0.95}

    if re.search(r"\b(what\s+date|today'?s?\s+date|current\s+date|what\s+day|today)\b", text):
        return {"intent": "get_date", "confidence": 0.95}

    # Timezone conversion
    tz_match = re.search(r"convert\s+(.+?)\s+from\s+(\w+)\s+to\s+(\w+)", text)
    if tz_match:
        return {
            "intent": "convert_timezone",
            "time": tz_match.group(1),
            "from_tz": tz_match.group(2),
            "to_tz": tz_match.group(3),
            "confidence": 0.90
        }

    # ============================================================
    # WEATHER
    # ============================================================
    weather_match = re.search(
        r"\b(weather|temperature|forecast|humid|raining|sunny|wind\s+speed)\b", text
    )
    if weather_match:
        # Try to extract city name
        city_match = re.search(
            r"\b(?:in|for|at|of)\s+([a-zA-Z\s]+?)(?:\s*$|\s+today|\s+now|\s+tomorrow)", text
        )
        city = city_match.group(1).strip() if city_match else None
        return {
            "intent": "get_weather",
            "city": city,
            "confidence": 0.90
        }

    # ============================================================
    # NEWS
    # ============================================================
    if re.search(r"\b(news|headlines|latest\s+news|top\s+stories|what'?s\s+happening)\b", text):
        # Detect category
        cat = "general"
        if re.search(r"\b(sport|cricket|football|soccer)\b", text):
            cat = "sports"
        elif re.search(r"\b(tech|technology|gadget|ai|software)\b", text):
            cat = "technology"
        elif re.search(r"\b(business|economy|market|stock)\b", text):
            cat = "business"
        elif re.search(r"\b(health|medical|covid|fitness)\b", text):
            cat = "health"
        elif re.search(r"\b(entertain|bollywood|hollywood|movie|film)\b", text):
            cat = "entertainment"
        return {"intent": "get_news", "category": cat, "confidence": 0.88}

    # ============================================================
    # CRYPTO
    # ============================================================
    crypto_match = re.search(
        r"\b(bitcoin|ethereum|dogecoin|litecoin|ripple|btc|eth|doge|xrp)\b", text
    )
    if crypto_match or re.search(r"\b(crypto|cryptocurrency|coin\s+price)\b", text):
        coin_map = {
            "btc": "bitcoin", "eth": "ethereum",
            "doge": "dogecoin", "xrp": "ripple"
        }
        coin_raw = crypto_match.group(1) if crypto_match else "bitcoin"
        coin = coin_map.get(coin_raw, coin_raw)
        currency = "inr"
        if re.search(r"\b(usd|dollar|dollars)\b", text):
            currency = "usd"
        elif re.search(r"\b(eur|euro)\b", text):
            currency = "eur"
        return {
            "intent": "get_crypto",
            "coin": coin,
            "currency": currency,
            "confidence": 0.90
        }

    # ============================================================
    # YOUTUBE
    # ============================================================
    if re.search(r"\b(youtube|search\s+video|watch\s+video|find\s+video)\b", text):
        query_match = re.search(
            r"(?:youtube|search|watch|find|play)\s+(?:video\s+)?(?:for\s+|about\s+)?(.+)", text
        )
        query = query_match.group(1).strip() if query_match else text
        return {"intent": "search_youtube", "query": query, "confidence": 0.88}

    # ============================================================
    # DICTIONARY
    # ============================================================
    dict_match = re.search(
        r"\b(meaning|define|definition|what\s+does\s+.+\s+mean|explain\s+word)\b", text
    )
    if dict_match:
        word_match = re.search(
            r"(?:meaning\s+of|define|definition\s+of|what\s+does\s+)(\w+)", text
        )
        word = word_match.group(1) if word_match else None
        return {"intent": "dictionary", "word": word, "confidence": 0.88}

    # ============================================================
    # OPEN APPLICATION
    # ============================================================
    if re.search(r"\bopen\b", text):
        after_open = re.split(r"\bopen\b", text, maxsplit=1)[1]
        ignore_words = {"app", "application", "named", "please", "for", "me", "the", "a", "an", "to"}
        words = after_open.strip().split()
        for word in words:
            if word not in ignore_words:
                return {"intent": "open_app", "app": word, "confidence": 0.90}

    # ============================================================
    # VOLUME CONTROL
    # ============================================================
    if re.search(r"\b(volume\s+up|increase\s+volume|louder|turn\s+up)\b", text):
        return {"intent": "volume_up", "confidence": 0.92}

    if re.search(r"\b(volume\s+down|decrease\s+volume|quieter|turn\s+down|lower\s+volume)\b", text):
        return {"intent": "volume_down", "confidence": 0.92}

    if re.search(r"\b(mute|silence|shut\s+up)\b", text):
        return {"intent": "mute", "confidence": 0.92}

    vol_set_match = re.search(r"\b(?:set|put)\s+volume\s+(?:to|at)\s+(\d+)\b", text)
    if vol_set_match:
        return {"intent": "set_volume", "level": int(vol_set_match.group(1)), "confidence": 0.93}

    if re.search(r"\bwhat.?s\s+the\s+volume\b", text):
        return {"intent": "get_volume", "confidence": 0.90}

    # ============================================================
    # BRIGHTNESS CONTROL
    # ============================================================
    if re.search(r"\b(brightness\s+up|increase\s+brightness|brighter)\b", text):
        return {"intent": "brightness_up", "confidence": 0.92}

    if re.search(r"\b(brightness\s+down|decrease\s+brightness|dimmer|dim\s+screen)\b", text):
        return {"intent": "brightness_down", "confidence": 0.92}

    bright_set_match = re.search(r"\b(?:set|put)\s+brightness\s+(?:to|at)\s+(\d+)\b", text)
    if bright_set_match:
        return {"intent": "set_brightness", "level": int(bright_set_match.group(1)), "confidence": 0.93}

    # ============================================================
    # SCREENSHOT
    # ============================================================
    if re.search(r"\b(screenshot|capture\s+screen|take\s+a\s+screenshot|screen\s+capture)\b", text):
        return {"intent": "take_screenshot", "confidence": 0.93}

    # ============================================================
    # MUSIC CONTROL
    # ============================================================
    if re.search(r"\b(play\s+music|play\s+song|start\s+music|play\s+some\s+music)\b", text):
        return {"intent": "play_music", "confidence": 0.90}

    if re.search(r"\b(stop\s+music|pause\s+music|stop\s+song|music\s+off)\b", text):
        return {"intent": "stop_music", "confidence": 0.90}

    # ============================================================
    # WINDOW MANAGEMENT
    # ============================================================
    if re.search(r"\b(minimize|minimise)\b", text):
        return {"intent": "minimize_window", "confidence": 0.88}

    if re.search(r"\b(maximize|maximise|full\s*screen)\b", text):
        return {"intent": "maximize_window", "confidence": 0.88}

    if re.search(r"\bclose\s+(this\s+)?(window|tab|app|application)\b", text):
        return {"intent": "close_window", "confidence": 0.88}

    if re.search(r"\brestore\s+window\b", text):
        return {"intent": "restore_window", "confidence": 0.88}

    # ============================================================
    # PROCESS MANAGEMENT
    # ============================================================
    proc_kill = re.search(r"\b(kill|end|terminate|stop)\s+(?:process\s+)?(.+)", text)
    if proc_kill:
        return {"intent": "kill_process", "process": proc_kill.group(2).strip(), "confidence": 0.88}

    if re.search(r"\b(list\s+processes|running\s+processes|what.?s\s+running)\b", text):
        return {"intent": "list_processes", "confidence": 0.88}

    # ============================================================
    # FILE MANAGER
    # ============================================================
    if re.search(r"\b(list\s+files|show\s+files|what.?s\s+in\s+(the\s+)?folder)\b", text):
        return {"intent": "list_files", "confidence": 0.87}

    create_folder = re.search(r"\bcreate\s+folder\s+(?:named?\s+)?(.+)", text)
    if create_folder:
        return {"intent": "create_folder", "name": create_folder.group(1).strip(), "confidence": 0.90}

    delete_match = re.search(r"\bdelete\s+(file|folder)?\s*(.+)", text)
    if delete_match:
        return {"intent": "delete_item", "name": delete_match.group(2).strip(), "confidence": 0.88}

    search_file = re.search(r"\bfind\s+file\s+(.+)", text)
    if search_file:
        return {"intent": "search_file", "name": search_file.group(1).strip(), "confidence": 0.88}

    # ============================================================
    # RUN CODE / TERMINAL
    # ============================================================
    if re.search(r"\b(run\s+command|terminal|cmd|powershell|command\s+prompt)\b", text):
        cmd_match = re.search(r"run\s+command\s+(.+)", text)
        return {
            "intent": "run_command",
            "command": cmd_match.group(1).strip() if cmd_match else "",
            "confidence": 0.87
        }

    # ============================================================
    # LOCATION / GPS
    # ============================================================
    if re.search(r"\b(my\s+location|where\s+am\s+i|current\s+location|gps)\b", text):
        return {"intent": "get_location", "confidence": 0.90}

    # ============================================================
    # SEND MESSAGE / SMS
    # ============================================================
    sms_match = re.search(r"\bsend\s+(?:message|sms|text)\s+to\s+(\w+)\s+(.+)", text)
    if sms_match:
        return {
            "intent": "send_sms",
            "to": sms_match.group(1),
            "message": sms_match.group(2).strip(),
            "confidence": 0.88
        }

    # ============================================================
    # NOTIFICATIONS
    # ============================================================
    if re.search(r"\b(read\s+notifications|show\s+notifications|any\s+notifications)\b", text):
        return {"intent": "read_notifications", "confidence": 0.88}

    # ============================================================
    # VAULT (SECURE STORAGE)
    # ============================================================
    if re.search(r"\b(vault|secure\s+storage|store\s+document|save\s+securely)\b", text):
        return {"intent": "vault_open", "confidence": 0.85}

    vault_store = re.search(r"\bstore\s+(.+?)\s+in\s+vault\b", text)
    if vault_store:
        return {"intent": "vault_store", "item": vault_store.group(1), "confidence": 0.88}

    vault_get = re.search(r"\bget\s+(.+?)\s+from\s+vault\b", text)
    if vault_get:
        return {"intent": "vault_retrieve", "item": vault_get.group(1), "confidence": 0.88}

    # ============================================================
    # MEMORY / RECALL
    # ============================================================
    if re.search(r"\b(remember|recall|what\s+did\s+i\s+say|last\s+conversation)\b", text):
        return {"intent": "recall_memory", "query": text, "confidence": 0.83}

    if re.search(r"\bremember\s+that\s+(.+)", text):
        mem_match = re.search(r"remember\s+that\s+(.+)", text)
        return {
            "intent": "save_memory",
            "content": mem_match.group(1) if mem_match else text,
            "confidence": 0.85
        }

    # ============================================================
    # AUTOMATION / REMINDERS
    # ============================================================
    reminder_match = re.search(
        r"\b(?:remind|set\s+(?:a\s+)?reminder)\b.*?(?:at|in|after)\s+(.+)", text
    )
    if reminder_match:
        return {
            "intent": "set_reminder",
            "details": text,
            "time_expr": reminder_match.group(1).strip(),
            "confidence": 0.87
        }

    if re.search(r"\b(alarm|wake\s+me)\b", text):
        return {"intent": "set_alarm", "details": text, "confidence": 0.85}

    if re.search(r"\b(schedule|add\s+task|to.?do|todo)\b", text):
        return {"intent": "schedule_task", "details": text, "confidence": 0.83}

    # ============================================================
    # SYSTEM INFO
    # ============================================================
    if re.search(r"\b(system\s+info|cpu\s+usage|ram\s+usage|battery|disk\s+space|system\s+status)\b", text):
        return {"intent": "system_info", "confidence": 0.90}

    # ============================================================
    # CALCULATOR
    # ============================================================
    calc_match = re.search(
        r"\b(?:calculate|compute|what\s+is|solve)\s+([\d\s\+\-\*\/\.\(\)\^%]+)", text
    )
    if calc_match:
        return {
            "intent": "calculate",
            "expression": calc_match.group(1).strip(),
            "confidence": 0.90
        }

    # Inline math expression (e.g. "45 + 78")
    if re.fullmatch(r"[\d\s\+\-\*\/\.\(\)\^%]+", text.strip()):
        return {"intent": "calculate", "expression": text.strip(), "confidence": 0.85}

    # ============================================================
    # ADVICE (before generic chat)
    # ============================================================
    if re.search(r"\b(best\s+time|good\s+time|ideal\s+time|when\s+should\s+i)\b", text):
        return {"intent": "chat", "text": text, "confidence": 0.75}

    # ============================================================
    # FALLBACK → GENERAL CHAT (LLM)
    # ============================================================
    return {
        "intent": "chat",
        "text": text,
        "confidence": 0.40
    }


# =========================
# HELPERS
# =========================

def _unknown_intent() -> Dict:
    return {"intent": "unknown", "confidence": 0.0}


# =========================
# DEBUG / SELF TEST
# =========================

if __name__ == "__main__":
    tests = [
        "what time is it",
        "what's today's date",
        "weather in Mumbai",
        "what's the temperature in Delhi today",
        "get me latest tech news",
        "bitcoin price in usd",
        "search youtube for lo-fi music",
        "define the word ephemeral",
        "open chrome",
        "volume up",
        "set volume to 70",
        "take a screenshot",
        "kill process chrome",
        "list running processes",
        "create folder named projects",
        "remind me at 8pm to drink water",
        "what's the cpu usage",
        "calculate 55 + 33 * 2",
        "how are you",
        "tell me a joke",
        "exit"
    ]

    for t in tests:
        result = detect_intent(t)
        print(f"  [{result['intent']:20s}] ← {t}")
