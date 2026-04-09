from __future__ import annotations

import re
from typing import Any

from system.laptop.app_launcher import canonicalize_app_name


class SlotFiller:
    def fill(self, *, intent: str, raw_text: str, normalized: str) -> dict[str, Any]:
        slots: dict[str, Any] = {}

        if intent == "open_app":
            app = self._extract_app(normalized)
            if app:
                slots["app"] = app

        elif intent in {"set_volume", "set_brightness"}:
            level = self._extract_level(normalized)
            if level is not None:
                slots["level"] = level

        elif intent == "get_weather":
            city_match = re.search(r"\b(?:in|for|at)\s+([a-z]+(?:\s+[a-z]+)?)", normalized)
            if city_match:
                slots["city"] = city_match.group(1).strip()

        elif intent == "get_news":
            slots["category"] = "general"
            for cat in ["business", "entertainment", "health", "science", "sports", "technology"]:
                if cat in normalized:
                    slots["category"] = cat
                    break

        elif intent in {"play_youtube", "search_youtube"}:
            strip_words = r"\b(play|open|watch|search|find|look up|youtube|yt|video|for|on)\b"
            field = "video" if intent == "play_youtube" else "query"
            slots[field] = re.sub(strip_words, "", normalized).strip()

        elif intent == "lookup_word":
            m = re.search(r"\bdefine\s+([a-z]{2,})\b", normalized)
            if not m:
                m = re.search(r"\b(?:meaning of|definition of)\s+([a-z]{2,})\b", normalized)
            if not m:
                m = re.search(r"\bwhat\s+does\s+([a-z]{2,})\s+mean\b", normalized)
            if m:
                slots["word"] = m.group(1)

        elif intent == "get_crypto_price":
            for cur in ["usd", "eur", "inr"]:
                if cur in normalized:
                    slots["currency"] = cur
                    break
            slots.setdefault("currency", "inr")
            symbol = self._extract_coin(normalized)
            if symbol:
                slots["symbol"] = symbol

        elif intent == "check_price_alert":
            slots["direction"] = "below" if "below" in normalized else "above"
            num = re.search(r"(\d+)", normalized)
            if num:
                slots["target_price"] = int(num.group(1))
            symbol = self._extract_coin(normalized)
            if symbol:
                slots["symbol"] = symbol
            for cur in ["usd", "eur", "inr"]:
                if cur in normalized:
                    slots["currency"] = cur
                    break
            slots.setdefault("currency", "inr")

        elif intent == "schedule_task":
            num_match = re.search(r"(\d+)\s*(second|minute|hour)", normalized)
            if num_match:
                val = int(num_match.group(1))
                unit = num_match.group(2)
                slots["delay_seconds"] = val * (60 if unit == "minute" else 3600 if unit == "hour" else 1)
            slots.setdefault("query", raw_text)

        elif intent in {"advice_time", "convert_timezone", "evaluate_trigger", "apply_rules"}:
            key = "topic" if intent == "advice_time" else "query"
            slots[key] = raw_text

        return slots

    def _extract_app(self, normalized: str) -> str | None:
        patterns = [r"\bopen\s+(.+)$", r"\blaunch\s+(.+)$", r"\bstart\s+(.+)$", r"\brun\s+(.+)$"]
        for pat in patterns:
            m = re.search(pat, normalized)
            if m:
                app = re.sub(r"\b(the|a|an|please|for|me|my|app|application)\b", "", m.group(1)).strip()
                if app:
                    return canonicalize_app_name(" ".join(app.split()[:5]))
        return None

    @staticmethod
    def _extract_level(normalized: str) -> int | None:
        if re.search(r"\b(max|full|maximum)\b", normalized):
            return 100
        if re.search(r"\b(min|mute|zero|silent)\b", normalized):
            return 0
        m = re.search(r"(\d{1,3})", normalized)
        if not m:
            return None
        return max(0, min(100, int(m.group(1))))

    @staticmethod
    def _extract_coin(normalized: str) -> str | None:
        for coin in ["bitcoin", "ethereum", "dogecoin", "litecoin", "ripple"]:
            if coin in normalized:
                return coin
        for ticker in ["btc", "eth", "doge"]:
            if re.search(rf"\b{ticker}\b", normalized):
                return ticker
        return None
