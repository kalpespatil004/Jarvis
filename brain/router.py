"""
Router
------
Executes actions based on detected intent.

This file does zero intent thinking.
It receives structured intent data and dispatches to services.
"""

from __future__ import annotations

from services.service_router import dispatch_intent


def route(intent_data: dict, return_response: bool = False):
    """
    Route intent to the correct action.

    If `return_response=True`, returns text for UI/API consumers.
    Otherwise speaks the response for voice mode.
    """
    reply = dispatch_intent(intent_data)

    if return_response:
        return reply

    from body.speak import speak

    speak(reply)

    if intent_data.get("intent") == "exit":
        raise SystemExit

    return reply
