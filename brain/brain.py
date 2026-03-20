import traceback
from brain.intent_engine import detect_intent
from brain.router import route
from body.listen import listen
from body.speak import speak


# ==================================================
# UI / TEXT MODE
# ==================================================
def process_text(command: str) -> str:

    try:
        if not command or not command.strip():
            return ""

        command = command.lower().strip()
        print(f"[BRAIN:UI] Heard: {command}")

        if command in ("exit", "shutdown", "quit", "goodbye"):
            return "Shutting down. Take care."

        intent_data = detect_intent(command)
        print(f"[BRAIN:UI] Intent: {intent_data}")

        # Confidence + unknown handling
        if intent_data["confidence"] < 0.5 or intent_data["intent"] == "unknown":
            return "I didn't understand that."

        response = route(intent_data, return_response=True)  # type: ignore
        return response or ""

    except Exception as e:
        print("[BRAIN:UI ERROR]", e)
        traceback.print_exc()
        return "Something went wrong."


# ==================================================
# VOICE MODE
# ==================================================
def brain_loop():


    while True:
        try:
            # 1. LISTEN
            command = listen()

            if not command:
                continue

            command = command.lower().strip()
            print(f"[BRAIN] Heard: {command}")

            # 2. EXIT
            if command in ("exit", "shutdown", "quit", "goodbye"):
                speak("Shutting down. Take care.")
                break

            # 3. THINK (ONLY ONCE)
            intent_data = detect_intent(command)
            print(f"[BRAIN] Intent: {intent_data}")

            # 4. VALIDATE
            if intent_data["confidence"] < 0.5 or intent_data["intent"] == "unknown":
                speak("I didn't understand that")
                continue

            # 5. ACT
            route(intent_data)

        except KeyboardInterrupt:
            speak("Manual interrupt detected. Powering off.")
            break

        except Exception as e:
            print("[BRAIN ERROR]", e)
            traceback.print_exc()
            speak("Something went wrong. Recovering.")


# ==================================================
# DEBUG
# ==================================================
if __name__ == "__main__":
    brain_loop()