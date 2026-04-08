from body.listen_whisper import listen as whisper_listen
from body.listen_vosk import listen as vosk_listen


def listen_command():
    """
    Listen ONLY for a single command.
    Used AFTER wake word.
    """

    print("[STT] Listening for command...")

    try:
        text = whisper_listen()

        if text and text.strip():
            return text

        print("[STT] Whisper failed → fallback to Vosk")

        return vosk_listen()

    except Exception as e:
        print("[STT ERROR]", e)
        return vosk_listen()


if __name__ == "__main__":
    while True:
        print("FINAL:", listen_command())