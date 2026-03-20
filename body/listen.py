from body.listen_whisper import listen as whisper_listen
from body.listen_vosk import listen as vosk_listen


def listen():

    print("[STT] Listening...")

    try:
        # 🔥 PRIMARY → Whisper
        text = whisper_listen()

        if text:
            return text

        print("[STT] Whisper failed → fallback to Vosk")

        # ⚡ FALLBACK → Vosk
        text = vosk_listen()

        return text

    except Exception as e:
        print("[STT ERROR]", e)
        print("[STT] Using Vosk fallback...")

        return vosk_listen()


if __name__ == "__main__":
    while True:
        print("FINAL:", listen())