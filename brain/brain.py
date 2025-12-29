"""
Jarvis Brain
------------
Central control logic for Jarvis.

Supports:
- Voice mode (continuous loop)
- UI/Text mode (single-turn processing)
"""

import traceback

from body.listen import listen
from body.speak import speak
from brain.intent_engine import detect_intent
from brain.router import route


# ==================================================
# UI / TEXT MODE (SAFE FOR GUI)
# ==================================================

def process_text(command: str) -> str:
    """
    Process a single text command and return response.
    Used by UI / Web / API.
    """

    try:
        if not command or not command.strip():
            return ""

        command = command.lower().strip()
        print(f"[BRAIN:UI] Heard: {command}")

        # Exit handling
        if command in ("exit", "shutdown", "quit", "goodbye"):
            return "Shutting down. Take care."

        # Intent detection
        intent_data = detect_intent(command)
        print(f"[BRAIN:UI] Intent: {intent_data}")

        # Route intent and get response
        response = route(intent_data, return_response=True) # type: ignore
        return response or ""

    except Exception as e:
        print("[BRAIN:UI ERROR]", e)
        traceback.print_exc()
        return "Something went wrong."


# ==================================================
# VOICE MODE (CONTINUOUS LOOP)
# ==================================================

def brain_loop():
    """
    Main Jarvis lifecycle loop.
    Voice-based, blocking, continuous.
    """

    while True:
        try:
            # 1. LISTEN
            command = listen()

            if not command:
                continue

            command = command.lower().strip()
            print(f"[BRAIN] Heard: {command}")

            # 2. EXIT SAFETY
            if command in ("exit", "shutdown", "quit", "goodbye"):
                speak("Shutting down. Take care.")
                break

            # 3. THINK
            intent_data = detect_intent(command)
            print(f"[BRAIN] Intent: {intent_data}")

            # 4. ACT
            route(intent_data)

        except KeyboardInterrupt:
            speak("Manual interrupt detected. Powering off.")
            break

        except Exception as e:
            print("[BRAIN ERROR]", e)
            traceback.print_exc()
            speak("Something went wrong. Recovering.")


# ==================================================
# DEBUG MODE
# ==================================================

if __name__ == "__main__":
    brain_loop()
