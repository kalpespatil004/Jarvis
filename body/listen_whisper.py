import os
import queue
import time
from collections import deque

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DEFAULT_MAX_DURATION = 8.0
DEFAULT_WAIT_TIMEOUT = 5.0
BLOCK_DURATION = 0.1
START_THRESHOLD = 0.015
SILENCE_TIMEOUT = 1.0
PRE_ROLL_BLOCKS = 4

_model = None


class WhisperListenError(RuntimeError):
    """Raised when Whisper command capture cannot produce usable speech."""


def _get_model():
    global _model
    if _model is not None:
        return _model

    print("[WHISPER] Loading model...")
    requested_device = os.getenv("JARVIS_WHISPER_DEVICE", "cpu").strip().lower() or "cpu"
    requested_model = os.getenv("JARVIS_WHISPER_MODEL", "base").strip() or "base"

    device = requested_device if requested_device in {"cpu", "cuda"} else "cpu"
    compute_type = "int8_float16" if device == "cuda" else "int8"

    print(f"[WHISPER] Using device={device}, model={requested_model}")
    _model = WhisperModel(
        requested_model,
        device=device,
        compute_type=compute_type,
    )

    return _model


def _record_command_audio(
    max_duration: float = DEFAULT_MAX_DURATION,
    wait_timeout: float = DEFAULT_WAIT_TIMEOUT,
) -> np.ndarray:
    block_size = int(SAMPLE_RATE * BLOCK_DURATION)
    audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=64)
    pre_roll: deque[np.ndarray] = deque(maxlen=PRE_ROLL_BLOCKS)

    def audio_callback(indata, frames, callback_time, status):
        if status:
            return
        block = indata.copy().reshape(-1)
        if not audio_queue.full():
            audio_queue.put(block)

    print("[WHISPER] Listening for command...")
    heard_speech = False
    heard_blocks: list[np.ndarray] = []
    silence_blocks = 0
    speech_deadline = time.monotonic() + wait_timeout
    hard_deadline = speech_deadline + max_duration

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=block_size,
        channels=1,
        dtype="float32",
        callback=audio_callback,
    ):
        while True:
            now = time.monotonic()
            if not heard_speech and now > speech_deadline:
                raise WhisperListenError("No speech detected after wake word.")
            if heard_speech and now > hard_deadline:
                break

            try:
                block = audio_queue.get(timeout=0.25)
            except queue.Empty:
                continue

            energy = float(np.abs(block).mean())

            if not heard_speech:
                pre_roll.append(block)
                if energy >= START_THRESHOLD:
                    heard_speech = True
                    heard_blocks.extend(pre_roll)
                    heard_blocks.append(block)
                    hard_deadline = time.monotonic() + max_duration
                continue

            heard_blocks.append(block)
            if energy < START_THRESHOLD * 0.7:
                silence_blocks += 1
            else:
                silence_blocks = 0

            if silence_blocks >= int(SILENCE_TIMEOUT / BLOCK_DURATION):
                break

    if not heard_blocks:
        raise WhisperListenError("No speech detected after wake word.")

    audio = np.concatenate(heard_blocks).astype("float32", copy=False)
    return audio


def listen(duration: int | float = DEFAULT_MAX_DURATION):
    start = time.time()

    audio = _record_command_audio(max_duration=float(duration))

    model = _get_model()
    segments, info = model.transcribe(
        audio,
        beam_size=1,
        language="en",
        vad_filter=True,
    )

    text = " ".join(seg.text for seg in segments).strip().lower()
    elapsed = time.time() - start

    if not text:
        return None

    if elapsed > (float(duration) + 8):
        print("[WHISPER] Too slow")
        return None

    if len(text) < 2:
        return None

    print("[WHISPER USER]:", text)
    return text


if __name__ == "__main__":
    while True:
        try:
            print(listen())
        except WhisperListenError as exc:
            print(f"[WHISPER ERROR] {exc}")
