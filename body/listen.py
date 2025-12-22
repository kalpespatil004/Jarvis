"""
Jarvis Realtime Listener
- Offline
- Low latency
- Command-focused
"""

import json
import queue
import sounddevice as sd
import torch
from vosk import Model, KaldiRecognizer

# =========================
# CONFIG
# =========================
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000


# Grammar-limited commands (VERY IMPORTANT)
COMMAND_GRAMMAR = [
    "open chrome",
    "open youtube",
    "play music",
    "stop music",
    "what time is it",
    "shutdown",
    "exit"
]

# =========================
# LOAD MODELS
# =========================
vosk_model = Model("C:\\Jarvis\\body\\vosk-model-en-in-0.5")

rec = KaldiRecognizer(
    vosk_model,
    SAMPLE_RATE,
    json.dumps(COMMAND_GRAMMAR)
)

# Silero VAD
# type: ignore
vad_model, vad_utils = torch.hub.load(repo_or_dir="snakers4/silero-vad",model="silero_vad",force_reload=False) # type: ignore
(get_speech_timestamps, _, read_audio, _, _) = vad_utils

audio_queue = queue.Queue()


# =========================
# AUDIO CALLBACK
# =========================
def audio_callback(indata, frames, time, status):
    if status:
        return
    audio_queue.put(bytes(indata))


# =========================
# LISTEN FUNCTION
# =========================
def listen():
    """
    Realtime command listener.
    Continuously listens and prints recognized commands.
    """

    print("Jarvis listening...")

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):
        while True:
            data = audio_queue.get()

            # Feed audio to Vosk
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()

                if text:
                    print("USER:", text)
                    return text   

# =========================
# DEBUG MODE
# =========================
if __name__ == "__main__":
    while True:
        listen()
