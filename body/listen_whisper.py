import time
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURATION = 3

_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model

    print("[WHISPER] Loading model...")
    try:
        _model = WhisperModel(
            "base",
            device="cuda",
            compute_type="int8_float16",
        )
    except Exception as exc:
        print(f"[WHISPER] CUDA init failed ({exc}). Falling back to CPU.")
        _model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
        )

    return _model


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

    model = _get_model()
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
