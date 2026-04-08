


# import os
# import tempfile
# import sounddevice as sd
# import soundfile as sf
# from TTS.api import TTS

# # Load model ONCE at startup (important for speed)
# _tts = TTS("tts_models/en/vctk/vits")
# _JARVIS_SPEAKER = "p226"   # your chosen voice

# def speak(text: str, verbose: bool = True):
#     """
#     Offline TTS using Coqui TTS.
#     Fixed male Jarvis voice: p230
#     """

#     if not text or not text.strip():
#         return

#     if verbose:
#         print(f"Jarvis: {text}")

#     # temp wav file
#     out_path = os.path.join(
#         tempfile.gettempdir(),
#         "jarvis_voice.wav"
#     )

#     # generate speech
#     _tts.tts_to_file(
#         text=text,
#         speaker=_JARVIS_SPEAKER,
#         file_path=out_path
#     )

#     # play audio
#     data, sr = sf.read(out_path)
#     sd.play(data, sr)
#     sd.wait()


"""
Jarvis TTS – Level 2 Upgrade
---------------------------
• Offline
• GPU accelerated
• Male voice
• Non-blocking TTS generation
• Windows-safe audio playback
• Model warm-up
• Standalone test support
"""
import warnings
warnings.filterwarnings("ignore")

import torch
import queue
import threading
import sounddevice as sd
from TTS.api import TTS
# ===============================
# CONFIG
# ===============================

MODEL_NAME = "tts_models/en/vctk/vits"
SAMPLE_RATE = 22050
USE_GPU = torch.cuda.is_available()

MALE_SPEAKERS_PRIORITY = [
    "p230", "p232", "p237", "p243",
    "p254", "p256", "p258", "p270",
    "p226", "p228"
]

# ===============================
# LOAD MODEL ONCE
# ===============================

print("[TTS] Initializing voice engine...")
_tts = TTS(MODEL_NAME, gpu=USE_GPU)

DEFAULT_SPEAKER = "p230"


# ===============================
# AUDIO QUEUE
# ===============================

_audio_queue = queue.Queue()
_audio_loop_started = False
_audio_loop_lock = threading.Lock()
_pending_jobs = 0
_pending_jobs_lock = threading.Lock()
_pending_jobs_event = threading.Event()
_pending_jobs_event.set()

# ===============================
# BACKGROUND TTS WORKER
# ===============================

def _mark_job_started() -> None:
    global _pending_jobs
    with _pending_jobs_lock:
        _pending_jobs += 1
        _pending_jobs_event.clear()


def _mark_job_done() -> None:
    global _pending_jobs
    with _pending_jobs_lock:
        _pending_jobs = max(0, _pending_jobs - 1)
        if _pending_jobs == 0:
            _pending_jobs_event.set()


def _tts_worker(text: str):
    if not text or not text.strip():
        _mark_job_done()
        return

    print(f"Jarvis: {text}")

    try:
        wav = _tts.tts(
            text=text,
            speaker=DEFAULT_SPEAKER
        )
        _audio_queue.put(wav)
    except Exception as exc:
        print(f"[TTS ERROR] Failed to synthesize speech: {exc}")
        _mark_job_done()

# ===============================
# PUBLIC SPEAK (NON-BLOCKING)
# ===============================

def speak(text: str):
    ensure_audio_loop_started()
    text = text.replace("*", "")
    _mark_job_started()
    threading.Thread(
        target=_tts_worker,
        args=(text,),
        daemon=True
    ).start()


def ensure_audio_loop_started():
    """
    Start audio playback loop once in a background daemon thread.
    Needed for UI mode where `audio_loop()` is not running in `main.py`.
    """
    global _audio_loop_started
    with _audio_loop_lock:
        if _audio_loop_started:
            return

        threading.Thread(target=audio_loop, daemon=True).start()
        _audio_loop_started = True

# ===============================
# AUDIO LOOP (MAIN THREAD)
# ===============================

def audio_loop():
    """
    Must run in main thread.
    Handles all playback safely.
    """
    while True:
        wav = _audio_queue.get()
        try:
            sd.play(wav, SAMPLE_RATE)
            sd.wait()
        except Exception as exc:
            print(f"[TTS ERROR] Failed during audio playback: {exc}")
        finally:
            _mark_job_done()


def wait_until_done(timeout: float | None = None) -> bool:
    """Block until all queued speech is synthesized and played."""
    return _pending_jobs_event.wait(timeout=timeout)

# ===============================
# WARM-UP (LEVEL 2)
# ===============================

def warm_up():
    """
    Prime GPU + model to remove first-lag.
    """
    print("[TTS] Warming up...")
    _tts.tts("System online.", speaker=DEFAULT_SPEAKER) # type: ignore
    print("[TTS] Warm-up complete.")

# ===============================
# STANDALONE TEST
# ===============================

if __name__ == "__main__":
    print("[TTS] Running standalone test")

    warm_up()

    speak("Hello. This is Jarvis. Text to speech is online.")
    # Start audio loop in main thread
    audio_loop()
