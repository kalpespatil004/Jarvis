import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000
BLOCK_SIZE = 4000

WAKE_WORDS = ["jarvis", "hey jarvis","hey " ,"bro", "buddy" ]

model = Model(r"body/vosk-model-en-in-0.5")

# 🔥 STRICT GRAMMAR
rec = KaldiRecognizer(model, SAMPLE_RATE, json.dumps(WAKE_WORDS))

audio_queue = queue.Queue(maxsize=20)


def callback(indata, frames, time, status):
    if status:
        return
    if not audio_queue.full():
        audio_queue.put(bytes(indata))


def listen_for_wake_word():
    print("[WAKE] Listening...")

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        print("[WAKE] Waiting for wake word...")
        while True:
            data = audio_queue.get()

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip().lower()

                # 🔥 STRICT MATCH
                if text in WAKE_WORDS:
                    print("[WAKE DETECTED]:", text)
                    rec.Reset()
                    return