import os
import queue
import time
from collections import deque

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# =========================
# CONFIG
# =========================
SAMPLE_RATE = 16000
DEFAULT_MAX_DURATION = 8.0
DEFAULT_WAIT_TIMEOUT = 5.0

BLOCK_DURATION = 0.1
PRE_ROLL_BLOCKS = 4

BASE_THRESHOLD = 0.01   # dynamic baseline
SILENCE_TIMEOUT = 1.0

_model = None


class WhisperListenError(RuntimeError):
    pass


# =========================
# MODEL LOADER
# =========================
def _get_model():
    global _model
    if _model is not None:
        return _model

    print("[WHISPER] Loading model...")

    device = "cuda" if os.getenv("JARVIS_WHISPER_DEVICE") == "cuda" else "cpu"
    model_name = os.getenv("JARVIS_WHISPER_MODEL", "base")

    compute = "int8_float16" if device == "cuda" else "int8"

    print(f"[WHISPER] device={device}, model={model_name}")

    _model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute,
    )

    return _model


# =========================
# AUDIO NORMALIZATION
# =========================
def _normalize_audio(audio: np.ndarray) -> np.ndarray:
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    return audio.astype("float32")


# =========================
# RECORD WITH SMART VAD
# =========================
def _record_command_audio(max_duration, wait_timeout):

    block_size = int(SAMPLE_RATE * BLOCK_DURATION)
    audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=64)
    pre_roll = deque(maxlen=PRE_ROLL_BLOCKS)

    def callback(indata, frames, time_info, status):
        if status:
            return
        if not audio_queue.full():
            audio_queue.put(indata.copy().reshape(-1))

    print("[WHISPER] Listening for command...")

    heard = False
    collected = []
    silence_blocks = 0

    energy_history = deque(maxlen=20)

    speech_deadline = time.monotonic() + wait_timeout
    hard_deadline = speech_deadline + max_duration

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=block_size,
        channels=1,
        dtype="float32",
        callback=callback,
    ):
        while True:
            now = time.monotonic()

            if not heard and now > speech_deadline:
                raise WhisperListenError("No speech detected.")

            if heard and now > hard_deadline:
                break

            try:
                block = audio_queue.get(timeout=0.25)
            except queue.Empty:
                continue

            energy = float(np.abs(block).mean())
            energy_history.append(energy)

            # 🔥 dynamic threshold
            dynamic_threshold = max(BASE_THRESHOLD, np.mean(energy_history) * 1.5)

            if not heard:
                pre_roll.append(block)

                if energy > dynamic_threshold:
                    heard = True
                    collected.extend(pre_roll)
                    collected.append(block)
                    hard_deadline = time.monotonic() + max_duration

                continue

            collected.append(block)

            if energy < dynamic_threshold * 0.6:
                silence_blocks += 1
            else:
                silence_blocks = 0

            if silence_blocks >= int(SILENCE_TIMEOUT / BLOCK_DURATION):
                break

    if not collected:
        raise WhisperListenError("Empty audio.")

    audio = np.concatenate(collected)
    return _normalize_audio(audio)


# =========================
# MAIN LISTEN
# =========================
def listen(duration=DEFAULT_MAX_DURATION):
    start = time.time()

    audio = _record_command_audio(duration, DEFAULT_WAIT_TIMEOUT)

    model = _get_model()

    segments, _ = model.transcribe(
        audio,
        beam_size=1,
        language="en",
        vad_filter=True,
    )

    text = " ".join(seg.text for seg in segments).strip().lower()

    elapsed = time.time() - start

    print(f"[DEBUG] Text: '{text}' | Time: {elapsed:.2f}s")

    # ✅ only reject truly empty
    if not text or text.strip() == "":
        return None

    # ❌ removed stupid filters
    # no length check
    # no aggressive timeout

    print("[WHISPER USER]:", text)
    return text


# =========================
# TEST
# =========================
if __name__ == "__main__":
    while True:
        try:
            print(listen())
        except WhisperListenError as e:
            print("[WHISPER ERROR]", e)