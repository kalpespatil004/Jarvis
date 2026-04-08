from __future__ import annotations
import traceback
import time

from body.listen import listen_command
from body.speak import speak
from body.wake_word import listen_for_wake_word

from brain.intent_engine import detect_intent
from brain.router import route

from brain.context import context
from brain.events import trigger_event

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

    # ---------- EVENT ----------
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
# TEXT MODE (UI / API)
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
# VOICE EXECUTION (SYNC)
# =========================
def _execute(command: str):

    try:
        cleaned = command.strip()
        print(f"[BRAIN] Heard → {cleaned}")

        intent_data = detect_intent(cleaned)

        # 🔥 NO ASYNC (prevents duplicate execution bugs)
        _handle_intent(intent_data, voice_mode=True)

    except Exception as exc:
        print("[BRAIN ERROR]", exc)
        traceback.print_exc()
        speak("Something went wrong.")


# =========================
# MAIN LOOP (STATE CONTROL)
# =========================
def brain_loop():

    speak("Jarvis online.")

    while True:
        try:
            # =========================
            # 🧠 IDLE MODE (WAIT FOR WAKE WORD)
            # =========================
            

            # prevent wake-word bleed into command
            time.sleep(0.5)

            # =========================
            # 🧠 ACTIVE MODE (ONE COMMAND ONLY)
            # =========================
            command = input("[BRAIN] Type a command: ").strip()
            if not command:
                print("[BRAIN] No command detected.")
                speak("I didn't catch that.")
                continue

            print(f"[BRAIN] Heard → {command}")

            # =========================
            # EXECUTE COMMAND
            # =========================
            _execute(command)

            # 🔥 AUTO RESET → back to wake mode

        except KeyboardInterrupt:
            speak("Shutting down.")
            break

        except Exception as exc:
            print("[BRAIN LOOP ERROR]", exc)
            traceback.print_exc()
            speak("System error.")
            time.sleep(1)


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    brain_loop()