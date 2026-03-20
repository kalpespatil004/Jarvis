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
from memory.user_data import set_preference, get_preference

# =========================
# CORE ROUTER
# =========================
def route(intent_data: dict, return_response: bool = False):

    intent = intent_data.get("intent")

    # =========================
    # EXIT
    # =========================
    if intent == "exit":
        return _respond("Shutting down.", return_response, exit_program=True)

    elif intent == "save_name":
        name = intent_data.get("name")
        set_preference("name", name)
        return _respond(f"Got it. Your name is {name}.", return_response)

    elif intent == "get_name":
        name = get_preference("name")

        if name:
            return _respond(f"Your name is {name}.", return_response)
        else:
            return _respond("I don't know your name yet.", return_response)
    # =========================
    # TIME
    # =========================
    elif intent == "get_time":
        now = datetime.datetime.now().strftime("%I:%M %p")
        return _respond(get_response("get_time", now), return_response)

    # =========================
    # DATE
    # =========================
    elif intent == "get_date":
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        return _respond(get_response("get_date", today), return_response)

    # =========================
    # OPEN APP
    # =========================
    elif intent == "open_app":
        app = intent_data.get("app")
        return _open_app(app, return_response)

    # =========================
    # MUSIC
    # =========================
    elif intent == "play_music":
        _play_music()
        return _respond(get_response("play_music"), return_response)

    elif intent == "stop_music":
        _stop_music()
        return _respond(get_response("stop_music"), return_response)

    # =========================
    # CHAT / ADVICE
    # =========================
    elif intent in ("chat", "advice_time"):
        reply = chat(intent_data.get("text", ""))
        return _respond(reply, return_response)

    # =========================
    # UNKNOWN (IMPORTANT FIX)
    # =========================
    elif intent == "unknown":
        return _respond(get_response("fallback"), return_response)

    # =========================
    # SAFETY NET
    # =========================
    return _respond(get_response("fallback"), return_response)


# ==================================================
# RESPONSE HANDLER (NEW - IMPORTANT)
# ==================================================
def _respond(text, return_response=False, exit_program=False):

    if return_response:
        return text

    speak(text)

    if exit_program:
        raise SystemExit


# ==================================================
# APP HANDLER
# ==================================================
def _open_app(app: str, return_response: bool = False):

    if not app:
        return _respond(get_response("fallback"), return_response)

    app = app.lower()

    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
    }

    # =========================
    # BROWSER HANDLING (FIXED)
    # =========================
    if app == "chrome":
        path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        return _launch_exe(path, app, return_response)

    if app == "edge":
        path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        return _launch_exe(path, app, return_response)

    # =========================
    # SIMPLE APPS
    # =========================
    exe = app_map.get(app)

    if exe:
        return _launch_exe(exe, app, return_response)

    return _respond(f"I don't know how to open {app}.", return_response)


def _launch_exe(path, app, return_response):
    try:
        subprocess.Popen(path)
        return _respond(get_response("open_app", app), return_response)
    except Exception:
        return _respond(f"Failed to open {app}.", return_response)


# ==================================================
# MUSIC
# ==================================================
def _play_music():

    music_dir = os.path.join(os.path.expanduser("~"), "Music")

    if not os.path.exists(music_dir):
        speak("Music folder not found.")
        return

    try:
        os.startfile(music_dir)
    except Exception:
        speak("Unable to play music.")


def _stop_music():

    players = ["wmplayer.exe", "vlc.exe"]

    for player in players:
        os.system(f"taskkill /im {player} /f >nul 2>&1")