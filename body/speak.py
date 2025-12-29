


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
import random
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

DEFAULT_SPEAKER = "p228"


# ===============================
# AUDIO QUEUE
# ===============================

_audio_queue = queue.Queue()

# ===============================
# BACKGROUND TTS WORKER
# ===============================

def _tts_worker(text: str):
    if not text or not text.strip():
        return

    print(f"Jarvis: {text}")

    wav = _tts.tts(
        text=text,
        speaker=DEFAULT_SPEAKER
    )

    _audio_queue.put(wav)

# ===============================
# PUBLIC SPEAK (NON-BLOCKING)
# ===============================

def speak(text: str):
    text = text.replace("*", "")
    threading.Thread(
        target=_tts_worker,
        args=(text,),
        daemon=True
    ).start()

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
        sd.play(wav, SAMPLE_RATE)
        sd.wait()

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
