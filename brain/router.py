"""
Router
------
Executes actions based on detected intent.

This file does ZERO thinking.
It trusts the intent engine and just does the job.

Supports:
- Voice mode (speaks)
- UI mode (returns text)
"""

import os
import subprocess
import datetime
import webbrowser

from body.speak import speak
from brain.response_picker import get_response
from LLM.chatbot import chat


def route(intent_data: dict, return_response: bool = False):
    """
    Route intent to the correct action.

    If return_response=True:
        → return text (for UI)
    Else:
        → speak text (for voice)
    """

    intent = intent_data.get("intent")

    # =========================
    # EXIT
    # =========================
    if intent == "exit":
        reply = "Shutting down."

        if return_response:
            return reply

        speak(reply)
        raise SystemExit

    # =========================
    # GET CURRENT TIME
    # =========================
    if intent == "get_time":
        now = datetime.datetime.now().strftime("%I:%M %p")
        reply = get_response("get_time", now)

        if return_response:
            return reply

        speak(reply)
        return

    # =========================
    # GET CURRENT DATE
    # =========================
    if intent == "get_date":
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        reply = get_response("get_date", today)

        if return_response:
            return reply

        speak(reply)
        return

    # =========================
    # OPEN APPLICATION
    # =========================
    if intent == "open_app":
        app = intent_data.get("app")

        if not app:
            reply = get_response("fallback")

            if return_response:
                return reply

            speak(reply)
            return

        return _open_app(app, return_response)

    # =========================
    # PLAY MUSIC
    # =========================
    if intent == "play_music":
        reply = get_response("play_music")

        if return_response:
            return reply

        speak(reply)
        _play_music()
        return

    # =========================
    # STOP MUSIC
    # =========================
    if intent == "stop_music":
        reply = get_response("stop_music")

        if return_response:
            return reply

        speak(reply)
        _stop_music()
        return

    # =========================
    # CHAT / ADVICE / UNKNOWN
    # =========================
    if intent in ("chat", "advice_time", "unknown"):
        reply = chat(intent_data.get("text", ""))

        if return_response:
            return reply

        speak(reply)
        return

    # =========================
    # SAFETY NET
    # =========================
    reply = get_response("fallback")

    if return_response:
        return reply

    speak(reply)


# ==================================================
# HELPERS
# ==================================================

def _open_app(app: str, return_response: bool = False):
    """
    Open common Windows applications safely.
    """

    app = app.lower()

    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "chrome": "chrome",
        "edge": "msedge"
    }

    # Browsers
    if app in ("chrome", "edge"):
        reply = get_response("open_app", app)

        if return_response:
            webbrowser.open(app)
            return reply

        speak(reply)
        webbrowser.open(app)
        return

    exe = app_map.get(app)

    if not exe:
        reply = f"I don't know how to open {app}."

        if return_response:
            return reply

        speak(reply)
        return

    try:
        subprocess.Popen(exe)
        reply = get_response("open_app", app)

        if return_response:
            return reply

        speak(reply)

    except Exception:
        reply = f"Failed to open {app}."

        if return_response:
            return reply

        speak(reply)


def _play_music():
    """
    Opens the default Music folder.
    """
    music_dir = os.path.join(
        os.path.expanduser("~"),
        "Music"
    )

    if not os.path.exists(music_dir):
        speak("Music folder not found.")
        return

    try:
        os.startfile(music_dir)
    except Exception:
        speak("Unable to play music.")


def _stop_music():
    """
    Stops common music players (basic but effective).
    """
    players = ["wmplayer.exe", "vlc.exe"]

    for player in players:
        os.system(f"taskkill /im {player} /f >nul 2>&1")
