"""
Router
------
Executes actions based on detected intent.

This file does ZERO thinking.
It trusts the intent engine and just does the job.
"""

import os
import subprocess
import datetime
import webbrowser

from body.speak import speak
from brain.response_picker import get_response
from LLM.chatbot import chat



def route(intent_data: dict):
    """
    Route intent to the correct action.
    """

    intent = intent_data.get("intent")

    # =========================
    # EXIT
    # =========================
    if intent == "exit":
        speak("Shutting down.")
        raise SystemExit

    # =========================
    # GET CURRENT TIME
    # =========================
    if intent == "get_time":
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(get_response("get_time", now))
        return

    # =========================
    # GET CURRENT DATE
    # =========================
    if intent == "get_date":
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        speak(get_response("get_date", today))
        return

    # =========================
    # OPEN APPLICATION
    # =========================
    if intent == "open_app":
        app = intent_data.get("app")

        if not app:
            speak(get_response("fallback"))
            return

        _open_app(app)
        return

    # =========================
    # PLAY MUSIC
    # =========================
    if intent == "play_music":
        speak(get_response("play_music"))
        _play_music()
        return

    # =========================
    # STOP MUSIC
    # =========================
    if intent == "stop_music":
        speak(get_response("stop_music"))
        _stop_music()
        return

    # =========================
    # CHAT / ADVICE / UNKNOWN
    # =========================
    if intent in ("chat", "advice_time", "unknown"):
        
        reply = chat(intent_data.get("text", ""))
        speak(reply)
        return

    # =========================
    # SAFETY NET
    # =========================
    speak(get_response("fallback"))


# =========================
# HELPERS
# =========================

def _open_app(app: str):
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
        speak(get_response("open_app", app))
        webbrowser.open(app)
        return

    exe = app_map.get(app)

    if not exe:
        speak(f"I don't know how to open {app}.")
        return

    try:
        subprocess.Popen(exe)
        speak(get_response("open_app", app))
    except Exception:
        speak(f"Failed to open {app}.")


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
