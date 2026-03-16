"""
wake_word.py  –  Wake-word detection stub
-----------------------------------------
Listens continuously for "Hey Jarvis" and triggers the main brain.

Backend options (in order of preference):
1. Porcupine (Picovoice) – best accuracy
2. Simple energy-threshold keyword spotter (offline fallback)
"""

import threading
import time

# ── Config ──────────────────────────────────────────────────
WAKE_WORD          = "hey jarvis"
SENSITIVITY        = 0.5
_wake_callbacks    = []
_running           = False


def on_wake(callback):
    """Register a callback to be called when wake word is detected."""
    _wake_callbacks.append(callback)


def _trigger_callbacks():
    for cb in _wake_callbacks:
        try:
            cb()
        except Exception:
            pass


def _simple_keyword_loop():
    """
    Fallback: listen for wake word via SpeechRecognition.
    Runs in background thread.
    """
    global _running
    try:
        import speech_recognition as sr
        rec = sr.Recognizer()
        rec.energy_threshold = 300
        rec.dynamic_energy_threshold = True

        print(f"[WAKE] Listening for '{WAKE_WORD}'...")
        while _running:
            try:
                with sr.Microphone() as source:
                    audio = rec.listen(source, timeout=5, phrase_time_limit=4)
                text = rec.recognize_google(audio).lower()
                if WAKE_WORD in text or "jarvis" in text:
                    print("[WAKE] Wake word detected!")
                    _trigger_callbacks()
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except Exception:
                time.sleep(1)
    except ImportError:
        print("[WAKE] SpeechRecognition not available for wake word detection.")


def start():
    """Start wake-word detection in a background thread."""
    global _running
    if _running:
        return
    _running = True
    t = threading.Thread(target=_simple_keyword_loop, daemon=True)
    t.start()
    print("[WAKE] Wake-word listener started.")


def stop():
    """Stop wake-word detection."""
    global _running
    _running = False
    print("[WAKE] Wake-word listener stopped.")
