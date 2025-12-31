import sys
import threading
from PyQt6.QtWidgets import QApplication
from ui.desktop.main_window import MainWindow
from body.speak import audio_loop, warm_up


def run():
    # Warm up TTS once
    warm_up()

    # Start audio playback loop in background
    threading.Thread(
        target=audio_loop,
        daemon=True
    ).start()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
