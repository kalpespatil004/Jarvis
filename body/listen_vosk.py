import json
import queue
from pathlib import Path

import sounddevice as sd
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000
BLOCK_SIZE = 4000
WAKE_PHRASES = ("hey jarvis", "wake up", "jarvis")
MODEL_PATH = Path(__file__).with_name("vosk-model-en-in-0.5")

_vosk_model = None


def _get_model() -> Model:
    global _vosk_model
    if _vosk_model is None:
        _vosk_model = Model(str(MODEL_PATH))
    return _vosk_model


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _matches_wake_phrase(text: str, wake_phrases: tuple[str, ...]) -> bool:
    normalized_text = _normalize_text(text)
    for phrase in wake_phrases:
        normalized_phrase = _normalize_text(phrase)
        if normalized_text == normalized_phrase:
            return True
        if normalized_text.startswith(normalized_phrase + " "):
            return True
    return False


def _make_recognizer(grammar: tuple[str, ...] | None = None) -> KaldiRecognizer:
    model = _get_model()
    if grammar:
        return KaldiRecognizer(model, SAMPLE_RATE, json.dumps(list(grammar)))
    return KaldiRecognizer(model, SAMPLE_RATE)


def _run_listen(recognizer: KaldiRecognizer, stop_event=None, wake_phrases: tuple[str, ...] | None = None, label: str = "VOSK"):
    audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=20)
    normalized_wake_phrases = tuple(_normalize_text(item) for item in (wake_phrases or ()))

    def audio_callback(indata, frames, callback_time, status):
        if status:
            return
        if not audio_queue.full():
            audio_queue.put(bytes(indata))

    print(f"[{label}] Listening...")
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        while True:
            if stop_event is not None and stop_event.is_set():
                recognizer.Reset()
                return None

            try:
                data = audio_queue.get(timeout=0.25)
            except queue.Empty:
                continue

            if not recognizer.AcceptWaveform(data):
                continue

            result = json.loads(recognizer.Result())
            text = _normalize_text(result.get("text", ""))
            if text and (
                not normalized_wake_phrases
                or _matches_wake_phrase(text, normalized_wake_phrases)
            ):
                print(f"[{label} USER]: {text}")
                recognizer.Reset()
                return text


def listen(stop_event=None):
    recognizer = _make_recognizer()
    return _run_listen(recognizer=recognizer, stop_event=stop_event, label="VOSK")


def listen_for_wake_word(wake_phrases: tuple[str, ...] = WAKE_PHRASES, stop_event=None):
    recognizer = _make_recognizer()
    return _run_listen(
        recognizer=recognizer,
        stop_event=stop_event,
        wake_phrases=wake_phrases,
        label="WAKE",
    )


if __name__ == "__main__":
    while True:
        detected = listen_for_wake_word()
        if detected:
            print("WAKE:", detected)
