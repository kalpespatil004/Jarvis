# main.py
import threading
from body.speak import audio_loop, warm_up
from brain.brain import brain_loop

if __name__ == "__main__":

    warm_up()

    threading.Thread(target=brain_loop, daemon=True).start()
    audio_loop()

    brain_loop() 