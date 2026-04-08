import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000
BLOCK_SIZE = 4000

vosk_model = Model(r"body/vosk-model-en-in-0.5")
rec = KaldiRecognizer(vosk_model, SAMPLE_RATE)

audio_queue = queue.Queue(maxsize=20)


def audio_callback(indata, frames, time, status):
    if status:
        return
    if not audio_queue.full():
        audio_queue.put(bytes(indata))


def listen(timeout=6):
    """
    General speech recognition (fallback when Whisper fails)
    """

    print("[VOSK] Listening...")

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):
        while True:
            try:
                data = audio_queue.get(timeout=timeout)
            except queue.Empty:
                print("[VOSK] Timeout")
                return None

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()

                if text:
                    print("[VOSK USER]:", text)
                    rec.Reset()
                    return text
                
if __name__ == "__main__":
    while True:
        print("VOSK FINAL:", listen())