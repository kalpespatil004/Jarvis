from __future__ import annotations
import traceback
import time

from brain.intent_engine import detect_intent
from brain.router import route

from brain.context import context
from brain.events import trigger_event
from utils.async_executor import run_async


CONFIDENCE_THRESHOLD = 0.6


# =========================
# INTENT HANDLER
# =========================
def _handle_intent(intent_data: dict, voice_mode: bool = False):

    intent = intent_data.get("intent", "unknown")
    confidence = intent_data.get("confidence", 0)

    print(f"[BRAIN] Intent → {intent} ({confidence})")

    # ---------- CONTEXT ----------
    context.update(intent_data)

    # ---------- EVENT TRIGGER ----------
    trigger_event("intent_detected", intent_data)

    # ---------- LOW CONFIDENCE ----------
    if confidence < CONFIDENCE_THRESHOLD:
        print("[BRAIN] Low confidence → fallback to chat")
        intent_data["intent"] = "chat"

    # ---------- EXECUTION ----------
    if voice_mode:
        route(intent_data)
    else:
        return route(intent_data, return_response=True)


# =========================
# UI PROCESS
# =========================
def process_text(command: str) -> str:

    if not command or not command.strip():
        return "Say something meaningful."

    try:
        cleaned = command.strip()
        print(f"[BRAIN:UI] Heard → {cleaned}")

        intent_data = detect_intent(cleaned)

        response = _handle_intent(intent_data, voice_mode=False)

        return response or "No response generated."

    except Exception as exc:
        print("[BRAIN:UI ERROR]", exc)
        traceback.print_exc()
        return "System error occurred."


# =========================
# VOICE EXECUTION
# =========================
def _execute(command: str):

    try:
        cleaned = command.strip()
        print(f"[BRAIN] Heard → {cleaned}")

        intent_data = detect_intent(cleaned)

        # ⚡ ASYNC EXECUTION
        run_async(_handle_intent, intent_data, True)

    except Exception as exc:
        print("[BRAIN ERROR]", exc)
        traceback.print_exc()

        from body.speak import speak
        speak("Something went wrong.")


# =========================
# MAIN LOOP
# =========================
def brain_loop():

    from body.listen import listen
    from body.speak import speak

    speak("Jarvis online.")

    idle = 0

    while True:
        try:
            command = listen()

            if not command:
                idle += 1
                if idle > 5:
                    print("[BRAIN] Idle...")
                    idle = 0
                continue

            idle = 0

            _execute(command)

        except KeyboardInterrupt:
            speak("Shutting down.")
            break

        except SystemExit:
            break

        except Exception as exc:
            print("[BRAIN LOOP ERROR]", exc)
            traceback.print_exc()
            speak("System error.")
            time.sleep(1)


if __name__ == "__main__":
    brain_loop()