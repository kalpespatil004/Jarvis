import time
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURATION = 3

print("[WHISPER] Loading model...")

model = WhisperModel(
    "base",
    device="cuda",
    compute_type="int8_float16"
)


def record_audio():
    print("[WHISPER] Listening...")
    audio = sd.rec(int(DURATION * SAMPLE_RATE),
                   samplerate=SAMPLE_RATE,
                   channels=1,
                   dtype='float32')
    sd.wait()
    return audio.flatten()


def listen():

    start = time.time()

    audio = record_audio()

    segments, info = model.transcribe(
        audio,
        beam_size=1,
        language="en"
    )

    text = " ".join([seg.text for seg in segments]).strip().lower()

    duration = time.time() - start

    # 🔥 fail conditions
    if not text:
        return None

    if duration > 4:
        print("[WHISPER] Too slow")
        return None

    if len(text) < 2:
        return None

    print("[WHISPER USER]:", text)
    return text


if __name__ == "__main__":
    while True:
        listen()