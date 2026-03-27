import os
import sys
import os
from pathlib import Path


def _load_stylesheet(app) -> None:
    """Load optional desktop stylesheet if present."""
    qss_path = Path(__file__).with_name("styles.qss")
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def _preload_voice_stack() -> None:
    """Preload STT/TTS stack before showing the UI window."""
    print("[UI] Preloading voice stack (listen + speak)...")

    # Preload listen path.
    try:
        from body.listen import listen as _listen  # noqa: F401
        print("[UI] Listen module preloaded.")

        # Whisper native init can hard-exit on some CUDA setups before raising Python exceptions.
        # Keep GUI startup safe by making model preload opt-in.
        preload_whisper = os.environ.get("JARVIS_PRELOAD_WHISPER_MODEL", "0") == "1"
        if preload_whisper:
            if os.environ.get("JARVIS_PRELOAD_WHISPER_CPU", "1") == "1":
                os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

            from body.listen_whisper import _get_model

            _get_model()
            print("[UI] Whisper model preloaded.")
        else:
            print("[UI] Whisper model preload skipped (set JARVIS_PRELOAD_WHISPER_MODEL=1 to enable).")
    except Exception as exc:
        print(f"[UI] Listen preload failed: {exc}")

    # Preload speak path.
    try:
        from body.speak import ensure_audio_loop_started, speak, warm_up

        ensure_audio_loop_started()
        warm_up()
        speak("System online.")
        print("[UI] Speak stack preloaded.")
    except Exception as exc:
        print(f"[UI] Speak preload failed: {exc}")


def run() -> int:
    # Qt FFmpeg on Windows can exhaust DXVA/D3D11 decode surfaces on some H264 assets,
    # producing repeating "Static surface pool size exceeded" errors.
    # Allow users to override externally; otherwise default to software decoding for stability.
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
