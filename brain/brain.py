from __future__ import annotations
import traceback
import time
import threading

from body.listen import listen_command
from body.speak import speak
from body.wake_word import listen_for_wake_word

from brain.intent_engine import detect_intent
from brain.router import route
from brain.dialogue_manager import dialogue_manager

from brain.context import context
from brain.events import trigger_event
from memory.conversation import (
    add_turn,
    clear_working_memory,
    get_nlu_context,
    set_working_memory,
)

CONFIDENCE_THRESHOLD = 0.6
PROCESS_LOCK = threading.Lock()
API_LOCK_WAIT_SECONDS = 30


# =========================
# INTENT HANDLER
# =========================
def _handle_intent(intent_data: dict, voice_mode: bool = False) -> str | None:

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

    # ---------- DIALOGUE MANAGEMENT ----------
    dialogue = dialogue_manager.handle(intent_data, context)

    if dialogue.action in {"follow_up", "cancelled"}:
        response = dialogue.response or "Please clarify."
        if voice_mode:
            speak(response)
        return response

    # ---------- EXECUTION ----------
    return route(dialogue.command, return_response=not voice_mode)


def _remember_exchange(
    user_text: str,
    assistant_text: str,
    *,
    intent_data: dict | None = None,
    status: str = "success",
    error: str | None = None,
):
    user_metadata = dict(intent_data or {})
    if status:
        user_metadata["execution_status"] = status
    assistant_metadata = {
        "status": status,
        "intent": user_metadata.get("intent"),
    }
    if error:
        assistant_metadata["error"] = error
    add_turn(
        user_text,
        assistant_text,
        user_metadata=user_metadata or None,
        assistant_metadata=assistant_metadata,
    )


# =========================
# TEXT MODE (UI / API)
# =========================
def process_text(command: str) -> str:

    if not command or not command.strip():
        return "Say something meaningful."

    cleaned = command.strip()
    acquired = PROCESS_LOCK.acquire(timeout=API_LOCK_WAIT_SECONDS)
    if not acquired:
        response = "Jarvis is still finishing the previous command. Try again in a moment."
        _remember_exchange(cleaned, response, status="busy")
        return response

    intent_data: dict | None = None
    response = "System error occurred."
    try:
        print(f"[BRAIN:UI] Heard → {cleaned}")
        set_working_memory(current_task={"mode": "text", "input": cleaned, "status": "nlu"})

        memory_context = get_nlu_context()
        intent_data = detect_intent(cleaned, memory_context=memory_context)
        set_working_memory(current_task={"mode": "text", "input": cleaned, "status": "routing", "intent": intent_data.get("intent")})

        response = _handle_intent(intent_data, voice_mode=False) or "No response generated."
        _remember_exchange(cleaned, response, intent_data=intent_data, status="success")
        clear_working_memory()
        return response

    except Exception as exc:
        print("[BRAIN:UI ERROR]", exc)
        traceback.print_exc()
        _remember_exchange(cleaned, response, intent_data=intent_data, status="error", error=str(exc))
        clear_working_memory()
        return response
    finally:
        if acquired:
            PROCESS_LOCK.release()


# =========================
# VOICE EXECUTION (SYNC)
# =========================
def _execute(command: str):

    acquired = PROCESS_LOCK.acquire(blocking=False)
    if not acquired:
        response = "Still processing the previous command. Please wait."
        speak(response)
        if command and command.strip():
            _remember_exchange(command.strip(), response, status="busy")
        return

    cleaned = command.strip()
    intent_data: dict | None = None
    response = "Something went wrong."
    try:
        print(f"[BRAIN] Heard → {cleaned}")
        set_working_memory(current_task={"mode": "voice", "input": cleaned, "status": "nlu"})

        memory_context = get_nlu_context()
        intent_data = detect_intent(cleaned, memory_context=memory_context)
        set_working_memory(current_task={"mode": "voice", "input": cleaned, "status": "routing", "intent": intent_data.get("intent")})

        # 🔥 NO ASYNC (prevents duplicate execution bugs)
        response = _handle_intent(intent_data, voice_mode=True) or "No response generated."
        _remember_exchange(cleaned, response, intent_data=intent_data, status="success")
        clear_working_memory()

    except SystemExit:
        response = "Shutting down, sir."
        _remember_exchange(cleaned, response, intent_data=intent_data, status="success")
        clear_working_memory()
        raise
    except Exception as exc:
        print("[BRAIN ERROR]", exc)
        traceback.print_exc()
        speak(response)
        _remember_exchange(cleaned, response, intent_data=intent_data, status="error", error=str(exc))
        clear_working_memory()
    finally:
        if acquired:
            PROCESS_LOCK.release()


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
