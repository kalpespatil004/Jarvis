"""High-level service dispatcher for Jarvis intents."""

from __future__ import annotations

from services.app_service import open_application_response
from services.chat_service import chat_response
from services.music_service import play_music_response, stop_music_response
from services.time_service import get_current_date_response, get_current_time_response


def dispatch_intent(intent_data: dict) -> str:
    intent = intent_data.get("intent", "unknown")

    if intent == "exit":
        return "Shutting down."
    if intent == "get_time":
        return get_current_time_response()
    if intent == "get_date":
        return get_current_date_response()
    if intent == "open_app":
        return open_application_response(intent_data.get("app"))
    if intent == "play_music":
        return play_music_response()
    if intent == "stop_music":
        return stop_music_response()
    if intent in {"chat", "advice_time", "unknown"}:
        return chat_response(intent_data.get("text", ""))

    return chat_response(intent_data.get("text", ""))
