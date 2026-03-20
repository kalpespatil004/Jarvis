"""
Jarvis Brain
------------
Central control logic for Jarvis.

Supports:
- Voice mode (continuous loop)
- UI/Text mode (single-turn processing)
"""

from __future__ import annotations

import traceback

from brain.intent_engine import detect_intent
from brain.router import route


def process_text(command: str) -> str:
    """
    Process a single text command and return response.
    Used by UI / Web / API.
    """
    try:
        if not command or not command.strip():
            return ""

        cleaned_command = command.strip()
        print(f"[BRAIN:UI] Heard: {cleaned_command}")

        intent_data = detect_intent(cleaned_command)
        print(f"[BRAIN:UI] Intent: {intent_data}")

        response = route(intent_data, return_response=True)
        return response or ""
    except Exception as exc:
        print("[BRAIN:UI ERROR]", exc)
        traceback.print_exc()
        return "Something went wrong."


def brain_loop():
    """Main Jarvis lifecycle loop for voice mode."""
    from body.listen import listen
    from body.speak import speak

    while True:
        try:
            command = listen()
            if not command:
                continue

            cleaned_command = command.strip()
            print(f"[BRAIN] Heard: {cleaned_command}")

            intent_data = detect_intent(cleaned_command)
            print(f"[BRAIN] Intent: {intent_data}")

            route(intent_data)
        except KeyboardInterrupt:
            speak("Manual interrupt detected. Powering off.")
            break
        except SystemExit:
            break
        except Exception as exc:
            print("[BRAIN ERROR]", exc)
            traceback.print_exc()
            speak("Something went wrong. Recovering.")


if __name__ == "__main__":
    brain_loop()
