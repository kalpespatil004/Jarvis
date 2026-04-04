from __future__ import annotations

import re
import json
from typing import Any

from LLM.offlineLLM import chat as llm_chat


# =========================
# AVAILABLE INTENTS (FOR LLM)
# =========================
AVAILABLE_INTENTS = [
    # Core
    "exit", "greeting", "chat",

    # Time & Date
    "get_time", "get_date", "advice_time", "convert_timezone",

    # System Control
    "open_app", "brightness_control", "volume_control",
    "window_control", "screenshot", "run_code",
    "file_manager", "process_manager",

    # Media
    "play_music", "stop_music",
    "play_youtube", "search_youtube",

    # Info Services
    "get_weather", "get_news",
    "lookup_word", "get_crypto_price",

    # Alerts & Automation
    "check_price_alert", "schedule_task",
    "evaluate_trigger", "apply_rules",

    # Music Intents
    "play_music", "stop_music", "resume_music",
    "next_track", "previous_track",
    "play_by_mood", "play_artist", "play_playlist",
]

# =========================
# APP STOPWORDS
# =========================
_APP_STOPWORDS = {"the", "a", "an", "please", "for", "me", "app", "application"}

_MOODS = [
    "sleeping", "sleep", "relax", "relaxing", "calm", "chill", "peaceful",
    "meditation", "focus", "study", "studying", "concentration", "work",
    "coding", "productive", "workout", "gym", "energy", "morning", "running",
    "dance", "party", "happy", "sad", "romantic", "love", "angry", "nostalgic",
    "lonely", "motivated", "lofi", "jazz", "classical", "pop", "rock", "rap",
    "bollywood", "punjabi", "devotional", "instrumental", "acoustic", "edm",
    "night", "evening", "afternoon"
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
    # EXIT
    # =========================
    if re.fullmatch(r"(?:exit|quit|shutdown|bye|goodbye|close jarvis)", normalized):
        return _intent("exit", raw_text, normalized, 1.0)

    # =========================
    # GREETING
    # =========================
    if re.fullmatch(r"(?:hey|hi|hello|hey jarvis|hi jarvis|hello jarvis)", normalized):
        return _intent("greeting", raw_text, normalized, 0.98)

    # =========================
    # TIME QUERY
    # =========================
    if re.search(r"\b(what\s+time\s+is\s+it|tell\s+me\s+the\s+time|current\s+time|time\s+now)\b", normalized):
        return _intent("get_time", raw_text, normalized, 0.96)

    # =========================
    # DATE QUERY
    # =========================
    if re.search(r"\b(what\s+date\s+is\s+it|today'?s\s+date|current\s+date|date\s+today|what day is it)\b", normalized):
        return _intent("get_date", raw_text, normalized, 0.96)

    # =========================
    # ADVICE TIME
    # =========================
    if re.search(r"\b(best time|good time|ideal time|when should i)\b", normalized):
        return _intent("advice_time", raw_text, normalized, 0.84, topic=raw_text)

    # =========================
    # TIMEZONE CONVERSION
    # e.g. "convert 5pm IST to UTC"
    # =========================
    if re.search(r"\b(convert|change)\b.*(time|timezone|zone)\b", normalized) or \
       re.search(r"\b(ist|utc|gmt|pst|est|cst)\b.*\bto\b.*\b(ist|utc|gmt|pst|est|cst)\b", normalized):
        return _intent("convert_timezone", raw_text, normalized, 0.85, query=raw_text)

    # =========================
    # WEATHER
    # e.g. "weather in pune", "what's the weather"
    # =========================
    if re.search(r"\b(weather|temperature|forecast|humidity|climate)\b", normalized):
        city_match = re.search(r"\b(?:in|for|at)\s+([a-z]+(?:\s+[a-z]+)?)", normalized)
        city = city_match.group(1).strip() if city_match else None
        return _intent("get_weather", raw_text, normalized, 0.93, city=city)

    # =========================
    # NEWS
    # e.g. "latest news", "show me tech news"
    # =========================
    if re.search(r"\b(news|headlines|top stories|latest updates)\b", normalized):
        category = "general"
        for cat in ["business", "entertainment", "health", "science", "sports", "technology"]:
            if cat in normalized:
                category = cat
                break
        return _intent("get_news", raw_text, normalized, 0.91, category=category)

    # =========================
    # DICTIONARY / WORD LOOKUP
    # e.g. "meaning of serendipity", "define eloquent"
    # =========================
    if re.search(r"\b(meaning of|define|definition of|what does .+ mean|look up)\b", normalized):
        word_match = re.search(r"\b(?:meaning of|define|definition of|look up)\s+([a-z]+)", normalized)
        word = word_match.group(1) if word_match else None
        return _intent("lookup_word", raw_text, normalized, 0.92, word=word)

    # =========================
    # CRYPTO PRICE
    # e.g. "bitcoin price", "ethereum in inr"
    # =========================
    _COINS = ["bitcoin", "ethereum", "dogecoin", "litecoin", "ripple", "btc", "eth", "doge"]
    if any(coin in normalized for coin in _COINS) or re.search(r"\b(crypto|coin)\b", normalized):
        coin_match = next((c for c in _COINS if c in normalized), "bitcoin")
        currency = "inr"
        for cur in ["usd", "eur", "inr"]:
            if cur in normalized:
                currency = cur
                break
        return _intent("get_crypto_price", raw_text, normalized, 0.92,
                       symbol=coin_match, currency=currency)

    # =========================
    # CRYPTO PRICE ALERT
    # e.g. "alert me when bitcoin goes above 5000000"
    # =========================
    if re.search(r"\b(alert|notify|tell me)\b.*(price|bitcoin|ethereum|crypto)\b", normalized) or \
       re.search(r"\b(price alert|when .+ (above|below|reaches))\b", normalized):
        direction = "below" if "below" in normalized else "above"
        price_match = re.search(r"(\d+)", normalized)
        target = int(price_match.group(1)) if price_match else None
        return _intent("check_price_alert", raw_text, normalized, 0.87,
                       direction=direction, target_price=target)

    # =========================
    # SCHEDULE TASK / REMINDER
    # e.g. "remind me in 10 seconds", "schedule after 5 minutes"
    # =========================
    if re.search(r"\b(remind|reminder|schedule|set timer|after|in)\b.*(second|minute|hour)\b", normalized):
        delay = 0
        num_match = re.search(r"(\d+)\s*(second|minute|hour)", normalized)
        if num_match:
            val = int(num_match.group(1))
            unit = num_match.group(2)
            delay = val * (60 if unit == "minute" else 3600 if unit == "hour" else 1)
        return _intent("schedule_task", raw_text, normalized, 0.88, delay_seconds=delay, query=raw_text)

    # =========================
    # YOUTUBE PLAY
    # e.g. "play despacito on youtube"
    # =========================
    if re.search(r"\b(play|open|watch)\b.*(youtube|yt)\b", normalized) or \
       re.search(r"\byoutube\b.*\b(play|open|watch)\b", normalized):
        query_match = re.sub(r"\b(play|open|watch|youtube|yt|video|on)\b", "", normalized).strip()
        return _intent("play_youtube", raw_text, normalized, 0.92, video=query_match)

    # =========================
    # YOUTUBE SEARCH
    # e.g. "search youtube for lofi music"
    # =========================
    if re.search(r"\b(search|find|look up)\b.*(youtube|yt)\b", normalized) or \
       re.search(r"\byoutube\b.*\b(search|find)\b", normalized):
        query_match = re.sub(r"\b(search|find|look up|youtube|yt|for)\b", "", normalized).strip()
        return _intent("search_youtube", raw_text, normalized, 0.92, query=query_match)

    # =========================
    # PLAY MUSIC
    # =========================

    # PLAY MUSIC
    if re.search(r"\b(play|start|resume)\b.*\b(music|song|songs|playlist|audio)\b", normalized):
        return _intent("play_music", raw_text, normalized, 0.91)

    # STOP MUSIC
    if re.search(r"\b(stop|pause)\b.*\b(music|song|songs|playlist|audio)\b", normalized):
        return _intent("stop_music", raw_text, normalized, 0.91)

    # RESUME MUSIC
    if re.search(r"\b(resume|continue|unpause)\b.*\b(music|song|play)\b", normalized):
        return _intent("resume_music", raw_text, normalized, 0.92)

   # NEXT TRACK
    
    if re.search(r"\b(next|skip|next song|next track)\b", normalized):
        return _intent("next_track", raw_text, normalized, 0.92)


    # PREVIOUS TRACK
    
    if re.search(r"\b(previous|prev|last song|go back|previous track)\b", normalized):
        return _intent("previous_track", raw_text, normalized, 0.92)

    # PLAY BY MOOD 

    if any(mood in normalized for mood in _MOODS):
        mood_match = next((m for m in _MOODS if m in normalized), None)
        return _intent("play_by_mood", raw_text, normalized, 0.91, mood=mood_match)

    # STOP MUSIC
    
    if re.search(r"\b(stop|pause)\b.*\b(music|song|songs|playlist|audio)\b", normalized):
        return _intent("stop_music", raw_text, normalized, 0.91)
    
    # PLAY ARTIST
    
    if re.search(r"\b(play|put on)\b.*\b(by|songs by|music by)\b", normalized):
        artist_match = re.sub(r"\b(play|put on|songs|music|by)\b", "", normalized).strip()
        return _intent("play_artist", raw_text, normalized, 0.90, artist=artist_match)

    # PLAY PLAYLIST OR GENRE

    if re.search(r"\bplaylist\b", normalized):
        genre = re.sub(r"\b(play|playlist|music|songs|jarvis)\b", "", normalized).strip()
        return _intent("play_playlist", raw_text, normalized, 0.90, genre=genre)

    # =========================
    # OPEN APP
    # =========================
    app_name = _extract_app_name(normalized)
    if app_name:
        return _intent("open_app", raw_text, normalized, 0.90, app=app_name)

    # =========================
    # BRIGHTNESS CONTROL
    # =========================
    if "brightness" in normalized:
        if "max" in normalized or "full" in normalized:
            return _intent("brightness_control", raw_text, normalized, 0.95, level=100)
        if "min" in normalized or "zero" in normalized:
            return _intent("brightness_control", raw_text, normalized, 0.95, level=0)
        match = re.search(r"(\d+)", normalized)
        if match:
            return _intent("brightness_control", raw_text, normalized, 0.9, level=int(match.group(1)))
        return _intent("brightness_control", raw_text, normalized, 0.7)

    # =========================
    # VOLUME CONTROL
    # =========================
    if "volume" in normalized:
        if "max" in normalized or "full" in normalized:
            return _intent("volume_control", raw_text, normalized, 0.95, level=100)
        if "min" in normalized or "mute" in normalized:
            return _intent("volume_control", raw_text, normalized, 0.95, level=0)
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

    if re.search(r"\bdelete\b", normalized):
        name = re.sub(r"\bdelete\b", "", normalized).strip()
        return _intent("file_manager", raw_text, normalized, 0.85, action="delete", name=name)

    if re.search(r"\b(rename|move|copy)\b", normalized):
        action_match = re.search(r"\b(rename|move|copy)\b", normalized)
        action = action_match.group(1) if action_match else "unknown"
        name = re.sub(r"\b(rename|move|copy)\b", "", normalized).strip()
        return _intent("file_manager", raw_text, normalized, 0.85, action=action, name=name)

    # =========================
    # PROCESS MANAGER
    # =========================
    if re.search(r"\b(kill|terminate|end)\b.*\b(process|task|app)\b", normalized):
        name = re.sub(r"\b(kill|terminate|end|process|task|app)\b", "", normalized).strip()
        return _intent("process_manager", raw_text, normalized, 0.88, action="kill", name=name)

    if re.search(r"\b(list|show)\b.*\b(process|processes|tasks)\b", normalized):
        return _intent("process_manager", raw_text, normalized, 0.88, action="list")

    # =========================
    # WINDOW CONTROL
    # =========================
    if "minimize" in normalized:
        return _intent("window_control", raw_text, normalized, 0.9, action="minimize")

    if "maximize" in normalized:
        return _intent("window_control", raw_text, normalized, 0.9, action="maximize")

    if re.search(r"\bclose\s+window\b", normalized):
        return _intent("window_control", raw_text, normalized, 0.9, action="close")

    # =========================
    # SCREENSHOT
    # =========================
    if "screenshot" in normalized or "take a snap" in normalized:
        return _intent("screenshot", raw_text, normalized, 0.9)

    # =========================
    # RUN CODE
    # =========================
    if re.search(r"\brun\s+python\b", normalized):
        file = re.sub(r"\brun\s+python\b", "", normalized).strip()
        return _intent("run_code", raw_text, normalized, 0.9, file=file)

    # =========================
    # EVALUATE TRIGGER (IF-THEN)
    # e.g. "if battery low then notify me"
    # =========================
    if re.search(r"\bif\b.+\bthen\b", normalized):
        return _intent("evaluate_trigger", raw_text, normalized, 0.80, query=raw_text)

    # =========================
    # APPLY RULES
    # =========================
    if re.search(r"\b(apply rules|run rules|check rules|automation rules)\b", normalized):
        return _intent("apply_rules", raw_text, normalized, 0.80, query=raw_text)

    # =========================
    # LLM FALLBACK
    # =========================
    return _llm_fallback(raw_text)


# =========================
# LLM INTENT CLASSIFIER
# =========================
def _llm_fallback(text: str) -> dict:

    prompt = f"""
You are an intent classifier for a personal AI assistant called Jarvis.

Available intents:
{AVAILABLE_INTENTS}

Return ONLY valid JSON with no extra text, no markdown, no explanation.

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

User: what is the price of ethereum in usd
Output:
{{"intent": "get_crypto_price", "parameters": {{"symbol": "ethereum", "currency": "usd"}}}}

User: weather in mumbai
Output:
{{"intent": "get_weather", "parameters": {{"city": "mumbai"}}}}

User: {text}
Output:
"""

    response = llm_chat(prompt)

    try:
        clean = re.sub(r"```(?:json)?|```", "", response).strip()
        parsed = json.loads(clean)
        return _intent(
            parsed.get("intent", "chat"),
            text,
            _normalize(text),
            0.6,
            **parsed.get("parameters", {})
        )
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
    patterns = [
        r"\bopen\s+(.+)$",
        r"\blaunch\s+(.+)$",
        r"\bstart\s+(.+)$",
        r"\brun\s+(.+)$"
    ]
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
    return {
        "intent": "unknown",
        "text": "",
        "normalized_text": "",
        "confidence": 0.0
    }


