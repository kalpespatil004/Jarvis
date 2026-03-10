import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from ui.desktop.main_window import MainWindow


def _load_stylesheet(app: QApplication) -> None:
    """Load optional desktop stylesheet if present."""
    qss_path = Path(__file__).with_name("styles.qss")
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def run() -> int:
    app = QApplication(sys.argv)
    _load_stylesheet(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
