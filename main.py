# main.py
import threading

from body.speak import audio_loop, warm_up
from brain.brain import brain_loop
from memory.firestore_sync import overwrite_local_conversation_from_cloud


def init_memory():
    if overwrite_local_conversation_from_cloud():
        print("[SYNC] Local conversation overwritten from Firestore")
    else:
        print("[SYNC] Keeping local conversation")


if __name__ == "__main__":
    init_memory()

    warm_up()

    threading.Thread(target=brain_loop, daemon=True).start()
    audio_loop()
