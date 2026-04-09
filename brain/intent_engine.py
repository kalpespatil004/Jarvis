from __future__ import annotations

import re
import json
from typing import Any

from LLM.offlineLLM import chat as llm_chat

from brain.context import context
from system.laptop.app_launcher import canonicalize_app_name


from brain.nlu.classifier import IntentClassifier
from brain.nlu.slot_filler import SlotFiller
from brain.nlu.schema import LLM_CLASSIFIER_INTENTS, LLM_CLASSIFIER_INTENTS_SET, REQUIRED_SLOTS


NLU_CLASSIFIER = IntentClassifier()
SLOT_FILLER = SlotFiller()

# Chat: conversational Q&A, trivia, explanations (not device commands or tool intents).
_CHAT_START = re.compile(
    r"^(what|who|whom|whose|why|how|when|where|which|"
    r"can you|could you|would you|will you|"
    r"tell me|explain|describe|discuss|"
    r"do you know|do you think|is it true|are you sure|"
    r"i want to know|i need to know|i wonder|i m curious|im curious|"
    r"give me|help me understand|walk me through)\b"
)
_CHAT_PHRASE = re.compile(
    r"\b("
    r"full form of|full name of|short for|stand for|stands for|"
    r"abbreviation (for|of)|acronym for|meaning of life|"
    r"how come|what happened|what s the story|what is the story|"
    r"reason (why|for)"
    r")\b"
)

# "What is the volume / current brightness" → get_* (not general chat).
_VOLUME_LEVEL_QUERY = re.compile(
    r"\b("
    r"current\s+volume|volume\s+level|volume\s+percentage|volume\s+now|"
    r"what\s+(is|s)\s+the\s+volume|what\s+s\s+the\s+volume|"
    r"how\s+loud\s+(is|are|s)|what\s+is\s+my\s+volume|get\s+volume"
    r")\b"
)
_BRIGHTNESS_LEVEL_QUERY = re.compile(
    r"\b("
    r"current\s+brightness|brightness\s+level|brightness\s+now|"
    r"what\s+(is|s)\s+the\s+brightness|what\s+s\s+the\s+brightness|"
    r"screen\s+brightness\s+(level|now|percentage)|what\s+is\s+my\s+brightness|get\s+brightness"
    r")\b"
)

# =========================
# APP STOPWORDS
# =========================
_APP_STOPWORDS = {"the", "a", "an", "please", "for", "me", "my", "app", "application"}

_MOODS = [
    "sleeping", "sleep", "relax", "relaxing", "calm", "chill", "peaceful",
    "meditation", "focus", "study", "studying", "concentration", "work",
    "coding", "productive", "workout", "gym", "energy", "morning", "running",
    "dance", "party", "happy", "sad", "romantic", "love", "angry", "nostalgic",
    "lonely", "motivated", "lofi", "jazz", "classical", "pop", "rock", "rap",
    "bollywood", "punjabi", "devotional", "instrumental", "acoustic", "edm",
    "night", "evening", "afternoon"
]


def _is_explanatory_chat(norm: str) -> bool:
    """True when the user is asking for an explanation / conversation, not a hardware command."""
    if _VOLUME_LEVEL_QUERY.search(norm) or _BRIGHTNESS_LEVEL_QUERY.search(norm):
        return False
    if _CHAT_START.match(norm) or _CHAT_PHRASE.search(norm):
        return True
    if re.match(r"^what\s+(is|are|was|were)\s+", norm):
        return True
    return False


def _try_dictionary_intent(raw: str, norm: str) -> dict[str, Any] | None:
    """
    Dictionary API: single-token lookups only (define X, meaning of X, what does X mean).
    Multi-word phrases ('what does the full name of jarvis mean') are not dictionary intents.
    """
    if "youtube" in norm or re.search(r"\byt\b", norm):
        return None
    m = re.search(r"\bdefine\s+([a-z]{2,})\b", norm)
    if m:
        return _intent("lookup_word", raw, norm, 0.92, word=m.group(1))
    m = re.search(r"\b(?:meaning of|definition of)\s+([a-z]{2,})\b", norm)
    if m:
        return _intent("lookup_word", raw, norm, 0.92, word=m.group(1))
    m = re.search(r"\bwhat\s+does\s+([a-z]{2,})\s+mean\b", norm)
    if m:
        return _intent("lookup_word", raw, norm, 0.92, word=m.group(1))
    m = re.search(r"^look\s+up\s+([a-z]{2,})\s*$", norm)
    if m:
        return _intent("lookup_word", raw, norm, 0.88, word=m.group(1))
    return None


def _clamp_level(value: int) -> int:
    return max(0, min(100, value))


_CRYPTO_LONG = ("bitcoin", "ethereum", "dogecoin", "litecoin", "ripple")
_CRYPTO_SHORT = ("btc", "eth", "doge")


def _first_crypto_coin_mention(norm: str) -> str | None:
    """Match coin names; short tickers use word boundaries (avoid 'eth' inside 'something')."""
    for c in _CRYPTO_LONG:
        if c in norm:
            return c
    for c in _CRYPTO_SHORT:
        if re.search(rf"\b{re.escape(c)}\b", norm):
            return c
    return None


def _resolve_active_domain_followup(raw: str, norm: str) -> dict[str, Any] | None:
    """
    Short follow-ups after volume/brightness commands, e.g. "set to 100%" without saying "volume".
    Skips when the utterance looks like explanatory chat ("what is 100%").
    """
    domain = context.active_domain
    if not domain:
        return None
    if _is_explanatory_chat(norm):
        return None
    if domain == "volume" and re.search(r"\bbrightness\b", norm):
        return None
    if domain == "brightness" and re.search(r"\bvolume\b", norm) and not re.search(
        r"\bbrightness\b", norm
    ):
        return None

    n = norm.strip()

    if domain == "volume":
        if re.search(
            r"\b(a bit louder|turn it up|turn up|more loud)\b", n
        ) or n == "louder":
            return _intent("volume_up", raw, norm, 0.91)
        if re.search(
            r"\b(a bit quieter|turn it down|turn down|less loud)\b", n
        ) or n == "quieter":
            return _intent("volume_down", raw, norm, 0.91)

        m = re.match(
            r"^(?:set|put|make)(?:\s+it)?\s+to\s+(max|full|maximum|min|mute|zero|silent)$",
            n,
        )
        if m:
            key = m.group(1)
            if key in ("max", "full", "maximum"):
                return _intent("set_volume", raw, norm, 0.93, level=100)
            return _intent("set_volume", raw, norm, 0.93, level=0)

        m = re.match(
            r"^(?:set|put|make)(?:\s+it)?\s+to\s+(\d{1,3})(?:\s*(?:%|percent))?$",
            n,
        )
        if m:
            return _intent(
                "set_volume",
                raw,
                norm,
                0.92,
                level=_clamp_level(int(m.group(1))),
            )
        m = re.match(
            r"^(?:set|put|make)(?:\s+it)?\s+at\s+(\d{1,3})(?:\s*(?:%|percent))?$",
            n,
        )
        if m:
            return _intent(
                "set_volume",
                raw,
                norm,
                0.92,
                level=_clamp_level(int(m.group(1))),
            )
        m = re.match(r"^(\d{1,3})(?:\s*(?:%|percent))?$", n)
        if m:
            return _intent(
                "set_volume",
                raw,
                norm,
                0.9,
                level=_clamp_level(int(m.group(1))),
            )
        if re.match(r"^(max|full|maximum)$", n):
            return _intent("set_volume", raw, norm, 0.93, level=100)
        if re.match(r"^(min|mute|zero|silent)$", n):
            return _intent("set_volume", raw, norm, 0.93, level=0)

    if domain == "brightness":
        if re.search(r"\b(a bit brighter|turn it up|turn up|brighter|more bright)\b", n) or n in (
            "brighter",
            "bright",
        ):
            return _intent("brightness_up", raw, norm, 0.91)
        if re.search(
            r"\b(a bit dimmer|turn it down|turn down|dimmer|less bright|darker)\b",
            n,
        ) or n in ("dimmer", "dim"):
            return _intent("brightness_down", raw, norm, 0.91)

        m = re.match(
            r"^(?:set|put|make)(?:\s+it)?\s+to\s+(max|full|maximum|min|zero)$",
            n,
        )
        if m:
            key = m.group(1)
            if key in ("max", "full", "maximum"):
                return _intent("set_brightness", raw, norm, 0.93, level=100)
            return _intent("set_brightness", raw, norm, 0.93, level=0)

        m = re.match(
            r"^(?:set|put|make)(?:\s+it)?\s+to\s+(\d{1,3})(?:\s*(?:%|percent))?$",
            n,
        )
        if m:
            return _intent(
                "set_brightness",
                raw,
                norm,
                0.92,
                level=_clamp_level(int(m.group(1))),
            )
        m = re.match(
            r"^(?:set|put|make)(?:\s+it)?\s+at\s+(\d{1,3})(?:\s*(?:%|percent))?$",
            n,
        )
        if m:
            return _intent(
                "set_brightness",
                raw,
                norm,
                0.92,
                level=_clamp_level(int(m.group(1))),
            )
        m = re.match(r"^(\d{1,3})(?:\s*(?:%|percent))?$", n)
        if m:
            return _intent(
                "set_brightness",
                raw,
                norm,
                0.9,
                level=_clamp_level(int(m.group(1))),
            )
        if re.match(r"^(max|full|maximum)$", n):
            return _intent("set_brightness", raw, norm, 0.93, level=100)
        if re.match(r"^(min|zero)$", n):
            return _intent("set_brightness", raw, norm, 0.93, level=0)

    return None


def _resolve_relative_date_followup(raw: str, norm: str) -> dict[str, Any] | None:
    """Handle short follow-ups around date/day queries, including common misspellings."""
    if context.get_last_intent() != "get_date":
        return None

    if re.search(r"\b(and\s+)?(tomorrow|tommorow|tomarow|tomarrows|tomorrows)\b", norm):
        return _intent("get_date", raw, norm, 0.95, date_ref="tomorrow")
    if re.search(r"\b(and\s+)?(today|todays|todays\s+day|today\s+day)\b", norm):
        return _intent("get_date", raw, norm, 0.95, date_ref="today")
    if re.search(r"\b(and\s+)?(yesterday|yestarday)\b", norm):
        return _intent("get_date", raw, norm, 0.95, date_ref="yesterday")
    return None


# =========================
# MAIN DETECTOR
# =========================
def _regex_fallback_intent(text: str) -> dict[str, Any] | None:

    if not text or not text.strip():
        return _unknown_intent()

    raw_text = text.strip()
    normalized = _normalize(raw_text)

    follow = _resolve_active_domain_followup(raw_text, normalized)
    if follow is not None:
        return follow

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
    if re.search(
        r"\b("
        r"what\s+time\s+is\s+it|what\s+is\s+the\s+time|what\s+s\s+the\s+time|"
        r"tell\s+me\s+the\s+time|current\s+time|time\s+now"
        r")\b",
        normalized,
    ):
        return _intent("get_time", raw_text, normalized, 0.96)

    # =========================
    # DATE QUERY
    # =========================
    if re.search(
        r"\b("
        r"what\s+date\s+is\s+it|what\s+is\s+the\s+date|what\s+is\s+today\s+s\s+date|"
        r"today\s+s\s+date|today'?s\s+date|current\s+date|date\s+today|"
        r"what\s+day\s+is\s+it|what\s+is\s+today\s+day|today\s+day|"
        r"date\s+tomorrow|what\s+is\s+tomorrow|tomorrow\s+date|tomorrow\s+day|tommorow|tomarow|tomarrows|tomorrows|todays\s+day"
        r")\b",
        normalized,
    ):
        date_ref = "today"
        if re.search(r"\b(tomorrow|tommorow|tomarow|tomarrows|tomorrows)\b", normalized):
            date_ref = "tomorrow"
        elif re.search(r"\b(yesterday|yestarday)\b", normalized):
            date_ref = "yesterday"
        return _intent("get_date", raw_text, normalized, 0.96, date_ref=date_ref)

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
    # CRYPTO PRICE
    # e.g. "bitcoin price", "ethereum in inr"
    # Short tickers (eth, btc, doge) must be word-boundary — avoid "eth" in "something".
    # =========================
    coin_match = _first_crypto_coin_mention(normalized)
    if coin_match is None and re.search(r"\b(crypto|coin)\b", normalized):
        coin_match = "bitcoin"
    if coin_match:
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
    # DICTIONARY (single-token only; after YouTube so "look up … on youtube" is not a word lookup)
    # =========================
    dict_hit = _try_dictionary_intent(raw_text, normalized)
    if dict_hit:
        return dict_hit

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
        post_actions: list[str] = []
        if "maximize" in normalized:
            post_actions.append("maximize")
        if "minimize" in normalized:
            post_actions.append("minimize")
        return _intent("open_app", raw_text, normalized, 0.90, app=app_name, post_actions=post_actions)

    # =========================
    # GET VOLUME / GET BRIGHTNESS (current level)
    # =========================
    if _VOLUME_LEVEL_QUERY.search(normalized):
        return _intent("get_volume", raw_text, normalized, 0.94)
    if _BRIGHTNESS_LEVEL_QUERY.search(normalized):
        return _intent("get_brightness", raw_text, normalized, 0.94)

    # =========================
    # VOLUME STEP
    # =========================
    if re.search(
        r"\b(volume\s+up|increase\s+volume|turn\s+up\s+(the\s+)?volume|louder|more\s+volume)\b",
        normalized,
    ):
        return _intent("volume_up", raw_text, normalized, 0.93)
    if re.search(
        r"\b(volume\s+down|decrease\s+volume|turn\s+down\s+(the\s+)?volume|quieter|less\s+volume)\b",
        normalized,
    ):
        return _intent("volume_down", raw_text, normalized, 0.93)

    # =========================
    # BRIGHTNESS STEP
    # =========================
    if re.search(
        r"\b(brightness\s+up|increase\s+brightness|brighter|more\s+brightness)\b",
        normalized,
    ):
        return _intent("brightness_up", raw_text, normalized, 0.93)
    if re.search(
        r"\b(brightness\s+down|decrease\s+brightness|dimmer|less\s+brightness)\b",
        normalized,
    ):
        return _intent("brightness_down", raw_text, normalized, 0.93)

    # =========================
    # SET BRIGHTNESS / SET VOLUME (same names as system/router.py)
    # =========================
    bright_explicit = "brightness" in normalized and not _is_explanatory_chat(normalized)
    bright_session = (
        context.active_domain == "brightness"
        and not _is_explanatory_chat(normalized)
        and "brightness" not in normalized
        and (
            re.search(r"\b(set|put|make)\b", normalized)
            or re.search(r"\b(max|full|min|zero)\b", normalized)
            or re.match(r"^(\d{1,3})(?:\s*(?:%|percent))?$", normalized.strip())
        )
    )
    if bright_explicit or bright_session:
        if "max" in normalized or "full" in normalized:
            return _intent("set_brightness", raw_text, normalized, 0.95, level=100)
        if "min" in normalized or "zero" in normalized:
            return _intent("set_brightness", raw_text, normalized, 0.95, level=0)
        match = re.search(r"(\d+)", normalized)
        if match:
            return _intent(
                "set_brightness",
                raw_text,
                normalized,
                0.9,
                level=_clamp_level(int(match.group(1))),
            )
        return _intent("set_brightness", raw_text, normalized, 0.7)

    vol_explicit = "volume" in normalized and not _is_explanatory_chat(normalized)
    vol_session = (
        context.active_domain == "volume"
        and not _is_explanatory_chat(normalized)
        and "volume" not in normalized
        and (
            re.search(r"\b(set|put|make)\b", normalized)
            or re.search(r"\b(max|full|min|mute|zero)\b", normalized)
            or re.match(r"^(\d{1,3})(?:\s*(?:%|percent))?$", normalized.strip())
        )
    )
    if vol_explicit or vol_session:
        if "max" in normalized or "full" in normalized:
            return _intent("set_volume", raw_text, normalized, 0.95, level=100)
        if "min" in normalized or "mute" in normalized:
            return _intent("set_volume", raw_text, normalized, 0.95, level=0)
        match = re.search(r"(\d+)", normalized)
        if match:
            return _intent(
                "set_volume",
                raw_text,
                normalized,
                0.9,
                level=_clamp_level(int(match.group(1))),
            )
        return _intent("set_volume", raw_text, normalized, 0.7)

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
    # WINDOW (aligned with system/router.py)
    # =========================
    if "minimize" in normalized:
        return _intent("minimize", raw_text, normalized, 0.9)

    if "maximize" in normalized:
        return _intent("maximize", raw_text, normalized, 0.9)

    if re.search(r"\bclose\s+window\b", normalized):
        return _intent("close", raw_text, normalized, 0.9)

    if re.search(r"\brestore\s+window\b", normalized) or normalized.strip() == "restore":
        return _intent("restore", raw_text, normalized, 0.88)

    focus_match = re.search(r"\bfocus\s+(?:on\s+)?(.+)$", normalized)
    if focus_match:
        fname = re.sub(r"\b(please|window|the)\b", "", focus_match.group(1)).strip()
        if fname:
            return _intent("focus", raw_text, normalized, 0.88, name=fname)

    if re.search(r"\bmove\s+window\b", normalized):
        return _intent("move_window", raw_text, normalized, 0.85)

    if re.search(r"\bresize\s+window\b", normalized):
        return _intent("resize_window", raw_text, normalized, 0.85)

    # =========================
    # SCREENSHOT
    # =========================
    if "screenshot" in normalized or "take a snap" in normalized:
        return _intent("take_screenshot", raw_text, normalized, 0.9)

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
    # CHAT — clear Q&A / explanation (everything above failed; do not guess a tool intent)
    # =========================
    if _is_explanatory_chat(normalized):
        return _intent("chat", raw_text, normalized, 0.9)

    # =========================
    # LLM INTENT CLASSIFIER (commands / ambiguous phrasing not matched above)
    # =========================
    return None


# =========================
# ORCHESTRATED DETECTOR
# =========================
def detect_intent(text: str) -> dict[str, Any]:

    if not text or not text.strip():
        return _unknown_intent()

    raw_text = text.strip()
    normalized = _normalize(raw_text)

    # deterministic quick checks (exit/safety)
    if re.fullmatch(r"(?:exit|quit|shutdown|bye|goodbye|close jarvis)", normalized):
        return _intent("exit", raw_text, normalized, 1.0, source="deterministic", model_confidence=1.0)

    if re.search(r"\b(emergency stop|panic stop|abort all)\b", normalized):
        return _intent("exit", raw_text, normalized, 0.98, source="deterministic", model_confidence=0.98)

    follow = _resolve_active_domain_followup(raw_text, normalized)
    if follow is not None:
        follow.setdefault("source", "context_followup")
        follow.setdefault("model_confidence", follow.get("confidence", 0.0))
        follow.setdefault("disambiguation_needed", False)
        return follow

    date_follow = _resolve_relative_date_followup(raw_text, normalized)
    if date_follow is not None:
        date_follow.setdefault("source", "context_followup")
        date_follow.setdefault("model_confidence", date_follow.get("confidence", 0.0))
        date_follow.setdefault("disambiguation_needed", False)
        return date_follow

    cls = NLU_CLASSIFIER.classify(raw_text, normalized)
    slots = SLOT_FILLER.fill(intent=cls.intent, raw_text=raw_text, normalized=normalized)

    required = REQUIRED_SLOTS.get(cls.intent, ())
    disambiguation_needed = any(not slots.get(key) for key in required)

    if cls.confidence >= 0.78 and not disambiguation_needed:
        return _intent(
            cls.intent,
            raw_text,
            normalized,
            cls.confidence,
            source=cls.source,
            model_confidence=cls.confidence,
            disambiguation_needed=False,
            **slots,
        )

    regex_hit = _regex_fallback_intent(raw_text)
    if regex_hit is not None:
        regex_hit["source"] = "regex_fallback"
        regex_hit["model_confidence"] = regex_hit.get("confidence", 0.0)
        regex_hit["disambiguation_needed"] = False
        return regex_hit

    if cls.confidence >= 0.62:
        return _intent(
            cls.intent,
            raw_text,
            normalized,
            cls.confidence,
            source=cls.source,
            model_confidence=cls.confidence,
            disambiguation_needed=disambiguation_needed,
            **slots,
        )

    llm = _llm_fallback(raw_text)
    llm["source"] = "llm_fallback"
    llm["model_confidence"] = llm.get("confidence", 0.0)
    llm["disambiguation_needed"] = False
    return llm


# =========================
# LLM INTENT CLASSIFIER
# =========================
def _llm_fallback(text: str) -> dict:

    prompt = f"""
You are an intent classifier for a personal AI assistant called Jarvis.

Allowed intents (exact strings only):
{LLM_CLASSIFIER_INTENTS}

Decision policy:
1) Prefer a specific tool intent only when the user is clearly giving a COMMAND or requesting a
   built-in service (open app, set volume, weather in a city, play music, reminder, etc.).
2) Use "chat" when the user wants conversation: opinions, stories, how/why questions, homework-style
   questions, "what should I…", small talk, or anything that is not clearly one of the tools above.
3) If unsure between a tool and "chat", choose "chat".
4) Never output "lookup_word" or any intent not in the allowed list.

Return ONLY valid JSON with no extra text, no markdown, no explanation.

Format:
{{
  "intent": "intent_name",
  "parameters": {{}}
}}

Examples:
User: set brightness to max
Output:
{{"intent": "set_brightness", "parameters": {{"level": 100}}}}

User: open chrome
Output:
{{"intent": "open_app", "parameters": {{"app": "chrome"}}}}

User: what is the price of ethereum in usd
Output:
{{"intent": "get_crypto_price", "parameters": {{"symbol": "ethereum", "currency": "usd"}}}}

User: weather in mumbai
Output:
{{"intent": "get_weather", "parameters": {{"city": "mumbai"}}}}

User: what is the full form of NASA and why was it created
Output:
{{"intent": "chat", "parameters": {{}}}}

User: {text}
Output:
"""

    response = llm_chat(prompt)

    try:
        clean = re.sub(r"```(?:json)?|```", "", response).strip()
        parsed = json.loads(clean)
        intent_name = parsed.get("intent", "chat")
        if intent_name == "lookup_word" or intent_name not in LLM_CLASSIFIER_INTENTS_SET:
            intent_name = "chat"
            params: dict[str, Any] = {}
        else:
            params = parsed.get("parameters", {}) or {}
        if intent_name == "open_app" and isinstance(params.get("app"), str):
            params = {**params, "app": canonicalize_app_name(params["app"])}
        return _intent(
            intent_name,
            text,
            _normalize(text),
            0.6,
            **params
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
        r"\brun\s+(.+)$",
    ]
    best: tuple[int, str] | None = None
    for p in patterns:
        for m in re.finditer(p, text):
            start, candidate = m.start(), m.group(1).strip()
            if best is None or start >= best[0]:
                best = (start, candidate)
    if not best:
        return None
    candidate = re.split(r"\b(and|then)\b", best[1], maxsplit=1)[0].strip()
    tokens = [t for t in candidate.split() if t not in _APP_STOPWORDS and t != "it"]
    if not tokens:
        return None
    raw_name = " ".join(tokens[:5])
    return canonicalize_app_name(raw_name)


def _intent(intent: str, raw: str, norm: str, confidence: float, **extra: Any) -> dict:
    data = {
        "intent": intent,
        "text": raw,
        "normalized_text": norm,
        "confidence": confidence,
        "source": "unknown",
        "model_confidence": confidence,
        "disambiguation_needed": False,
    }
    data.update(extra)
    return data


def _unknown_intent() -> dict:
    return {
        "intent": "unknown",
        "text": "",
        "normalized_text": "",
        "confidence": 0.0,
        "source": "none",
        "model_confidence": 0.0,
        "disambiguation_needed": True,
    }


