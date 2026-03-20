"""
Router
------
Executes actions based on detected intent.

Brain decides WHAT to do.
Services handle HOW to do it.
"""

from __future__ import annotations

from brain.response_picker import get_response
from services.app_service import open_application_response
from services.chat_service import chat_response
from services.music_service import play_music_response, stop_music_response
from services.time_service import get_current_date_response, get_current_time_response

from services.service_router import dispatch_intent

# =========================
# CORE ROUTER
# =========================
def route(intent_data: dict, return_response: bool = False):
    """
    Route intent to the correct service.

    If `return_response=True`, returns text for UI/API consumers.
    Otherwise speaks the response for voice mode.
    """
    intent = intent_data.get("intent", "unknown")

    if intent == "exit":
        reply = "Shutting down."
    elif intent == "get_time":
        reply = get_current_time_response()
    elif intent == "get_date":
        reply = get_current_date_response()
    elif intent == "open_app":
        reply = open_application_response(intent_data.get("app"))
    elif intent == "play_music":
        reply = play_music_response()
    elif intent == "stop_music":
        reply = stop_music_response()
    elif intent in {"chat", "advice_time", "unknown"}:
        reply = chat_response(intent_data.get("text", ""))
    else:
        reply = get_response("fallback")

    if return_response:
        return reply

    from body.speak import speak

    speak(reply)

    if intent == "exit":
        raise SystemExit

    return reply
