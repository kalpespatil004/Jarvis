import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000
BLOCK_SIZE = 4000

COMMAND_GRAMMAR = [
    "open chrome",
    "open youtube",
    "play music",
    "stop music",
    "what time is it",
    "shutdown",
    "exit"
]

vosk_model = Model("C:\\Jarvis\\body\\vosk-model-en-in-0.5")

rec = KaldiRecognizer(
    vosk_model,
    SAMPLE_RATE,
    json.dumps(COMMAND_GRAMMAR)
)

audio_queue = queue.Queue(maxsize=20)


def audio_callback(indata, frames, time, status):
    if status:
        return

    if not audio_queue.full():
        audio_queue.put(bytes(indata))


def listen():

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

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()

                if text:
                    print("USER:", text)
                    rec.Reset()
                    return text


if __name__ == "__main__":

    while True:
        listen()