"""
service_router.py
-----------------
Central router: maps intent → correct service
"""

# Weather
from services.weather.weather_api import get_weather
from services.weather.formatter import format_weather

# News
from services.news.news_api import get_news

# Crypto
from services.crypto.crypto_api import get_crypto_price
from services.crypto.price_alerts import check_price_alert

# Time & Date
from services.time_date.time_utils import current_time
from services.time_date.timezone import convert_timezone

# YouTube
from services.youtube.search import search_youtube
from services.youtube.play import play_video

# Dictionary
from services.dictionary.dictionary_api import lookup_word
from services.dictionary.meanings import format_meanings


def route(intent: str, **kwargs):
    """
    Route intent to appropriate service.

    Args:
        intent (str): Action keyword
        kwargs: Parameters for the service

    Returns:
        Any: Service response
    """

    if not intent or not isinstance(intent, str):
        return "❌ Invalid intent"

    intent = intent.lower().strip()

    # ================= WEATHER =================
    if intent == "weather":
        city = kwargs.get("city")
        data = get_weather(city)
        return format_weather(data)

    # ================= NEWS =================
    if intent == "news":
        return get_news(
            category=kwargs.get("category", "general"),
            country=kwargs.get("country", "in"),
            limit=kwargs.get("limit", 5)
        )

    # ================= CRYPTO =================
    if intent == "crypto":
        return get_crypto_price(
            symbol=kwargs.get("symbol", "bitcoin"),
            currency=kwargs.get("currency", "inr")
        )

    if intent == "crypto_alert":
        return check_price_alert(
            current_price=kwargs.get("current_price"),
            target_price=kwargs.get("target_price"),
            direction=kwargs.get("direction", "above")
        )

    # ================= TIME =================
    if intent == "time":
        return current_time()

    if intent == "timezone":
        return convert_timezone(
            kwargs.get("time"),
            kwargs.get("from_tz"),
            kwargs.get("to_tz")
        )

    # ================= YOUTUBE =================
    if intent == "youtube":
        return search_youtube(kwargs.get("query"))

    if intent == "play":
        return play_video(kwargs.get("video"))

    # ================= DICTIONARY =================
    if intent == "dictionary":
        result = lookup_word(kwargs.get("word"))
        return format_meanings(result)

    # ================= UNKNOWN =================
    return f"❌ Unknown intent: {intent}"
