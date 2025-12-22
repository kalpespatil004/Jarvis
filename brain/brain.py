"""
Jarvis Brain
------------
Central control loop of Jarvis.
Coordinates:
- Listening (ears)
- Thinking (intent detection)
- Speaking (mouth)
"""

from body.listen import listen
from body.speak import speak
from brain.intent_engine import detect_intent
from brain.router import route
import traceback


def brain_loop():
    """
    Main Jarvis lifecycle loop.
    This function never returns unless Jarvis is shut down.
    """

    speak("Jarvis online. Systems stable.")

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

            # 3. THINK (INTENT)
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


# =========================
# DEBUG RUN
# =========================
if __name__ == "__main__":
    brain_loop()
