# brain/router.py

from body.speak import speak
import datetime
import os

def route(intent_data: dict):
    intent = intent_data["intent"]

    if intent == "get_time":
        now = datetime.datetime.now().strftime("%H:%M")
        speak(f"The time is {now}")

    elif intent == "open_app":
        app = intent_data.get("app", "")
        speak(f"Opening {app}")
        # later: os.startfile or subprocess

    elif intent == "chat":
        speak("I heard you. Intelligence update pending.")
