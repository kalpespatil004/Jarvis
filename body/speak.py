"""
speak.py  –  Jarvis TTS (cross-platform, non-blocking)
-------------------------------------------------------
• Primary  : Coqui TTS (offline, GPU-aware, male voice)
• Fallback : pyttsx3  (no-dependency offline TTS)
• Audio queue for non-blocking playback
• Warm-up to remove first-speak lag
"""

import warnings
warnings.filterwarnings("ignore")

import queue
import threading
import sys

# ── Config ──────────────────────────────────────────────────
try:
    from config import TTS_MODEL, TTS_SPEAKER, TTS_SAMPLE_RATE, USE_GPU
except ImportError:
    TTS_MODEL       = "tts_models/en/vctk/vits"
    TTS_SPEAKER     = "p228"
    TTS_SAMPLE_RATE = 22050
    USE_GPU         = "auto"

# ── Resolve GPU flag ────────────────────────────────────────
if USE_GPU == "auto":
    try:
        import torch
        _USE_GPU = torch.cuda.is_available()
    except ImportError:
        _USE_GPU = False
elif USE_GPU == "true":
    _USE_GPU = True
else:
    _USE_GPU = False

# ── Try loading Coqui TTS ────────────────────────────────────
_tts = None
_tts_backend = "none"

try:
    from TTS.api import TTS as CoquiTTS
    import sounddevice as sd
    _tts = CoquiTTS(TTS_MODEL, gpu=_USE_GPU)
    _tts_backend = "coqui"
    print(f"[TTS] Coqui TTS loaded (GPU={_USE_GPU}, speaker={TTS_SPEAKER})")
except Exception as e:
    print(f"[TTS] Coqui unavailable ({e}), trying pyttsx3...")
    try:
        import pyttsx3
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 170)
        _engine.setProperty("volume", 0.9)
        # Pick a male voice if available
        voices = _engine.getProperty("voices")
        for v in voices:
            if "male" in v.name.lower() or "david" in v.name.lower() or "mark" in v.name.lower():
                _engine.setProperty("voice", v.id)
                break
        _tts_backend = "pyttsx3"
        print("[TTS] pyttsx3 loaded as fallback TTS.")
    except Exception as e2:
        print(f"[TTS] pyttsx3 also unavailable ({e2}). TTS disabled.")
        _tts_backend = "print_only"

# ── Audio Queue (Coqui only) ─────────────────────────────────
_audio_queue: queue.Queue = queue.Queue()
_loop_started = False
_loop_lock = threading.Lock()


# ============================================================
# PUBLIC API
# ============================================================

def speak(text: str):
    """
    Speak text using best available TTS engine.
    Non-blocking for Coqui; blocking for pyttsx3.
    """
    if not text or not text.strip():
        return

    text = text.replace("*", "").replace("#", "").strip()
    print(f"Jarvis: {text}")

    if _tts_backend == "coqui":
        _ensure_audio_loop()
        threading.Thread(target=_coqui_worker, args=(text,), daemon=True).start()

    elif _tts_backend == "pyttsx3":
        threading.Thread(target=_pyttsx3_worker, args=(text,), daemon=True).start()

    # "print_only" → already printed above


def warm_up():
    """Prime TTS model to eliminate first-speak delay."""
    if _tts_backend == "coqui":
        print("[TTS] Warming up Coqui...")
        try:
            _tts.tts("System online.", speaker=TTS_SPEAKER)  # type: ignore
            print("[TTS] Warm-up complete.")
        except Exception as e:
            print(f"[TTS] Warm-up failed: {e}")
    elif _tts_backend == "pyttsx3":
        print("[TTS] pyttsx3 ready (no warm-up needed).")
    else:
        print("[TTS] No TTS engine available.")


def audio_loop():
    """
    Main-thread audio playback loop (Coqui only).
    Call from main.py in voice mode.
    """
    if _tts_backend != "coqui":
        # Keep thread alive for voice mode even without coqui
        import time
        while True:
            time.sleep(1)
        return

    while True:
        wav = _audio_queue.get()
        try:
            import sounddevice as sd
            sd.play(wav, TTS_SAMPLE_RATE)
            sd.wait()
        except Exception as e:
            print(f"[TTS] Playback error: {e}")


# ============================================================
# INTERNALS
# ============================================================

def _coqui_worker(text: str):
    try:
        wav = _tts.tts(text, speaker=TTS_SPEAKER)  # type: ignore
        _audio_queue.put(wav)
    except Exception as e:
        print(f"[TTS] Synthesis error: {e}")


def _pyttsx3_worker(text: str):
    try:
        _engine.say(text)  # type: ignore
        _engine.runAndWait()
    except Exception as e:
        print(f"[TTS] pyttsx3 error: {e}")


def _ensure_audio_loop():
    """Start audio loop in background if not already running."""
    global _loop_started
    with _loop_lock:
        if _loop_started:
            return
        threading.Thread(target=audio_loop, daemon=True).start()
        _loop_started = True


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    warm_up()
    speak("Hello. Jarvis is online and ready.")
    audio_loop()
