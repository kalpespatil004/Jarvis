import sys
import os
from pathlib import Path


def _load_stylesheet(app) -> None:
    """Load optional desktop stylesheet if present."""
    qss_path = Path(__file__).with_name("styles.qss")
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


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

    from ui.desktop.main_window import MainWindow

    app = QApplication(sys.argv)
    _load_stylesheet(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
