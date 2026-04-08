import os
import sys
from pathlib import Path


def _load_stylesheet(app) -> None:
    """Load optional desktop stylesheet if present."""
    qss_path = Path(__file__).with_name("styles.qss")
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def _preload_voice_stack() -> None:
    """Preload the same STT/TTS path used by the desktop UI before showing the window."""
    print("[UI] Preloading voice stack (desktop listen + speak)...")

    try:
        from body.listen import listen as _listen  # noqa: F401
        from body.listen_whisper import _get_model

        _get_model()
        print("[UI] Listen stack preloaded.")
    except Exception as exc:
        print(f"[UI] Listen preload failed: {exc}")

    try:
        if os.environ.get("JARVIS_USE_EDGE_TTS", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "edge",
        ):
            from body.speak_edgetts import ensure_audio_loop_started, warm_up
        else:
            from body.speak import ensure_audio_loop_started, warm_up

        ensure_audio_loop_started()
        warm_up()
        print("[UI] Speak stack preloaded.")
    except Exception as exc:
        print(f"[UI] Speak preload failed: {exc}")


def run() -> int:
    if sys.platform.startswith("win"):
        os.environ.setdefault("QT_FFMPEG_DECODING_HW_DEVICE_TYPES", "")

    try:
        from PyQt6.QtWidgets import QApplication
    except ModuleNotFoundError:
        print("PyQt6 is not installed. Run: pip install pyqt6")
        return 1

    _preload_voice_stack()

    from ui.desktop.main_window import MainWindow

    app = QApplication(sys.argv)
    _load_stylesheet(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
