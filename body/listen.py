"""
listen.py  –  Cross-platform Speech-to-Text
--------------------------------------------
• Primary  : Vosk (offline, fast)
• Fallback : SpeechRecognition + Google API (online)
• Falls back gracefully if microphone not available
"""

import os
import json
import queue

# ── Config ──────────────────────────────────────────────────
try:
    from config import VOSK_MODEL_PATH, STT_SAMPLE_RATE, STT_BLOCK_SIZE
except ImportError:
    VOSK_MODEL_PATH = r"C:\Jarvis\body\vosk-model-en-in-0.5"
    STT_SAMPLE_RATE = 16000
    STT_BLOCK_SIZE  = 4000

# ── Try loading Vosk ─────────────────────────────────────────
_vosk_ready = False
_vosk_rec   = None

try:
    from vosk import Model, KaldiRecognizer
    import sounddevice as sd

    if os.path.exists(VOSK_MODEL_PATH):
        _model    = Model(VOSK_MODEL_PATH)
        _vosk_rec = KaldiRecognizer(_model, STT_SAMPLE_RATE)
        _vosk_ready = True
        print(f"[STT] Vosk loaded from {VOSK_MODEL_PATH}")
    else:
        print(f"[STT] Vosk model not found at {VOSK_MODEL_PATH}. Trying fallback.")
except ImportError:
    print("[STT] Vosk not installed. Trying SpeechRecognition fallback.")
except Exception as e:
    print(f"[STT] Vosk init error: {e}")

# ── Try SpeechRecognition (fallback) ─────────────────────────
_sr_ready = False
_recognizer = None

if not _vosk_ready:
    try:
        import speech_recognition as sr
        _recognizer = sr.Recognizer()
        _sr_ready = True
        print("[STT] SpeechRecognition loaded as fallback.")
    except ImportError:
        print("[STT] SpeechRecognition not installed. STT disabled.")

# ── Audio queue (Vosk) ───────────────────────────────────────
_audio_queue: queue.Queue = queue.Queue(maxsize=20)


def _audio_callback(indata, frames, time, status):
    if not _audio_queue.full():
        _audio_queue.put(bytes(indata))


# ============================================================
# PUBLIC API
# ============================================================

def listen(timeout: int = 10) -> str:
    """
    Listen for a voice command and return transcribed text.
    Returns empty string if nothing heard or on error.
    """
    if _vosk_ready:
        return _listen_vosk()
    elif _sr_ready:
        return _listen_sr(timeout)
    else:
        # Text input fallback (useful for testing)
        return _listen_text()


# ============================================================
# BACKENDS
# ============================================================

def _listen_vosk() -> str:
    """Offline Vosk speech recognition."""
    import sounddevice as sd
    print("[STT] Listening (Vosk)...")

    try:
        _vosk_rec.Reset()  # type: ignore
        with sd.RawInputStream(
            samplerate=STT_SAMPLE_RATE,
            blocksize=STT_BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=_audio_callback
        ):
            while True:
                data = _audio_queue.get()
                if _vosk_rec.AcceptWaveform(data):  # type: ignore
                    result = json.loads(_vosk_rec.Result())  # type: ignore
                    text = result.get("text", "").strip()
                    if text:
                        print(f"[STT] Heard: {text}")
                        _vosk_rec.Reset()  # type: ignore
                        return text
    except Exception as e:
        print(f"[STT] Vosk error: {e}")
        return ""


def _listen_sr(timeout: int = 10) -> str:
    """Online SpeechRecognition fallback (Google API)."""
    import speech_recognition as sr
    print("[STT] Listening (SpeechRecognition)...")

    try:
        with sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.5)  # type: ignore
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=8)  # type: ignore

        text = _recognizer.recognize_google(audio)  # type: ignore
        text = text.lower().strip()
        print(f"[STT] Heard: {text}")
        return text

    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"[STT] Google API error: {e}")
        return ""
    except Exception as e:
        print(f"[STT] SpeechRecognition error: {e}")
        return ""


def _listen_text() -> str:
    """Text input fallback when no STT engine is available."""
    try:
        text = input("You (type): ").strip().lower()
        return text
    except (EOFError, KeyboardInterrupt):
        return "exit"


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    while True:
        result = listen()
        if result:
            print(f"Transcribed: {result}")
            if result in ("exit", "quit"):
                break
