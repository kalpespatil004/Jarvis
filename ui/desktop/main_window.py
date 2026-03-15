from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, QTimer, Qt, QUrl, QSizeF, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPalette
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from brain.brain import process_text
from ui.desktop.tts_bridge import speak_text
from ui.desktop.voice_input import VoiceInputError, capture_voice_text


class BrainWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        response = process_text(self.text)
        self.finished.emit(response or "")


class ListenWorker(QObject):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def run(self):
        try:
            text = capture_voice_text()
            self.success.emit(text)
        except VoiceInputError as exc:
            self.error.emit(str(exc))


class MainWindow(QWidget):
    AVATAR_DIR_CANDIDATES = ("avatar", "avtar")

    VIDEO_NAME_CANDIDATES = {
        "idle": ["idle.mp4"],
        "listening": ["listening.mp4"],
        "thinking": ["thinking.mp4"],
        "speaking": ["speaking.mp4"],
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")

        self._brain_thread: QThread | None = None
        self._brain_worker: BrainWorker | None = None
        self._listen_thread: QThread | None = None
        self._listen_worker: ListenWorker | None = None

        self.avatar_state = "idle"
        self.video_paths = self._resolve_video_paths()

        self.player = QMediaPlayer(self)
        # Intentionally no audio output for avatar videos (silent animation only).

        self.video_item = QGraphicsVideoItem()
        self.player.setVideoOutput(self.video_item)

        # Loop current state video forever.
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_player_error)

        self.init_ui()
        self._apply_video_geometry_hint()
        self.set_avatar_state("idle")

    def _resolve_video_paths(self) -> dict[str, Path]:
        project_root = Path(__file__).resolve().parents[2]
        search_dirs = [project_root / "assets" / name for name in self.AVATAR_DIR_CANDIDATES]
        resolved: dict[str, Path] = {}

        for state, candidates in self.VIDEO_NAME_CANDIDATES.items():
            for folder in search_dirs:
                for name in candidates:
                    path = folder / name
                    if path.exists():
                        resolved[state] = path
                        break
                if state in resolved:
                    break

        self._avatar_search_dirs = search_dirs
        return resolved

    def _apply_video_geometry_hint(self):
        # Keep fixed window size based on avatar resolution (fallback to 560x840).
        try:
            import cv2  # type: ignore

            probe = self.video_paths.get("idle") or next(iter(self.video_paths.values()))
            cap = cv2.VideoCapture(str(probe))
            ok, frame = cap.read()
            cap.release()
            if ok and frame is not None:
                height, width = frame.shape[:2]
                controls_height = 72
                self.setFixedSize(width, height + controls_height)
                return
        except Exception:
            pass

        self.setFixedSize(560, 912)

    def init_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setFrameShape(QFrame.Shape.NoFrame)
        self.graphics_view.setStyleSheet("background: black;")

        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)

        self.scene.addItem(self.video_item)

        from PyQt6.QtGui import QPen

        self.subtitle_bg = QGraphicsRectItem()
        self.subtitle_bg.setBrush(QBrush(QColor(0, 0, 0, 190)))
        self.subtitle_bg.setPen(QPen(Qt.PenStyle.NoPen))
        self.subtitle_bg.setZValue(1)
        self.scene.addItem(self.subtitle_bg)

        self.subtitle_text = QGraphicsTextItem("Jarvis: Online.")
        font = QFont()
        font.setPointSize(18)
        font.setWeight(QFont.Weight.DemiBold)
        self.subtitle_text.setDefaultTextColor(QColor("white"))
        self.subtitle_text.setFont(font)
        self.subtitle_text.setTextWidth(600)
        self.subtitle_text.setZValue(2)
        self.scene.addItem(self.subtitle_text)

        controls = QWidget(self)
        controls.setFixedHeight(72)
        controls.setObjectName("controlsPanel")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(10, 8, 10, 8)
        controls_layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type a command...")
        self.input_box.returnPressed.connect(self.send_message)

        self.listen_btn = QPushButton("Listen")
        self.listen_btn.clicked.connect(self.listen_once)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        controls_layout.addWidget(self.input_box, 1)
        controls_layout.addWidget(self.listen_btn)
        controls_layout.addWidget(self.send_btn)

        root.addWidget(self.graphics_view, 1)
        root.addWidget(controls, 0)
        self.setLayout(root)

        self.setStyleSheet(
            """
            QWidget { background: #05070a; color: #e6edf3; }
            #controlsPanel { background: #0f1419; border-top: 1px solid #30363d; }
            QLineEdit {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background: #238636;
                color: white;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 14px;
            }
            QPushButton:disabled { background: #2d333b; color: #8b949e; }
            """
        )

        palette = self.graphics_view.palette()
        palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.black)
        self.graphics_view.setPalette(palette)
        self.graphics_view.setAutoFillBackground(True)
        self._layout_subtitle()

    def _layout_subtitle(self):
        if not hasattr(self, "scene"):
            return

        view_rect = self.graphics_view.viewport().rect()
        self.scene.setSceneRect(0, 0, view_rect.width(), view_rect.height())
        self.video_item.setSize(QSizeF(view_rect.width(), view_rect.height()))
        self.video_item.setPos(0, 0)

        margin_x = 16
        bottom_margin = 14
        max_width = max(200, view_rect.width() - margin_x * 2)

        self.subtitle_text.setTextWidth(max_width)
        doc = self.subtitle_text.document()
        text_size = doc.size()

        width = min(max_width, text_size.width())
        height = max(56, text_size.height())
        x = margin_x
        y = max(0, view_rect.height() - height - bottom_margin)

        self.subtitle_text.setPos(x, y)
        self.subtitle_bg.setRect(x - 8, y - 8, width + 16, height + 16)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_subtitle()

    def showEvent(self, event):
        super().showEvent(event)
        self._layout_subtitle()

    def _set_inputs_enabled(self, enabled: bool):
        self.send_btn.setDisabled(not enabled)
        self.listen_btn.setDisabled(not enabled)
        self.input_box.setDisabled(not enabled)
        if enabled:
            self.input_box.setFocus()

    def _set_subtitle(self, speaker: str, text: str):
        self.subtitle_text.setPlainText(f"{speaker}: {text}")
        self._layout_subtitle()

    def set_avatar_state(self, state: str):
        self.avatar_state = state
        source = self.video_paths.get(state) or self.video_paths.get("idle")

        if source is None:
            search_hint = ", ".join(str(p) for p in self._avatar_search_dirs)
            self._set_subtitle("Jarvis", f"Avatar videos not found. Checked: {search_hint}")
            return

        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(source)))
        self.player.play()

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    def _on_player_error(self, _error):
        message = self.player.errorString() or "Unable to render avatar video."
        self._set_subtitle("Jarvis", f"Video error: {message}")

    def listen_once(self):
        if self._listen_thread is not None or self._brain_thread is not None:
            return

        self.set_avatar_state("listening")
        self._set_subtitle("Jarvis", "Listening...")
        self._set_inputs_enabled(False)

        self._listen_thread = QThread(self)
        self._listen_worker = ListenWorker()
        self._listen_worker.moveToThread(self._listen_thread)

        self._listen_thread.started.connect(self._listen_worker.run)
        self._listen_worker.success.connect(self._on_listen_success)
        self._listen_worker.error.connect(self._on_listen_error)
        self._listen_worker.success.connect(self._listen_thread.quit)
        self._listen_worker.error.connect(self._listen_thread.quit)
        self._listen_worker.success.connect(self._listen_worker.deleteLater)
        self._listen_worker.error.connect(self._listen_worker.deleteLater)
        self._listen_thread.finished.connect(self._listen_thread.deleteLater)
        self._listen_thread.finished.connect(self._on_listen_complete)
        self._listen_thread.start()

    def _on_listen_success(self, text: str):
        self.input_box.setText(text)
        self._set_subtitle("You", text)
        self.send_message()

    def _on_listen_error(self, message: str):
        self._set_subtitle("Jarvis", f"Listen error: {message}")
        self.set_avatar_state("idle")

    def _on_listen_complete(self):
        self._listen_thread = None
        self._listen_worker = None
        if self._brain_thread is None:
            self._set_inputs_enabled(True)

    def send_message(self):
        text = self.input_box.text().strip()
        if not text or self._brain_thread is not None:
            return

        self.input_box.clear()
        self._set_subtitle("You", text)
        self.set_avatar_state("thinking")
        self._set_inputs_enabled(False)

        self._brain_thread = QThread(self)
        self._brain_worker = BrainWorker(text)
        self._brain_worker.moveToThread(self._brain_thread)

        self._brain_thread.started.connect(self._brain_worker.run)
        self._brain_worker.finished.connect(self._handle_response)
        self._brain_worker.finished.connect(self._brain_thread.quit)
        self._brain_worker.finished.connect(self._brain_worker.deleteLater)
        self._brain_thread.finished.connect(self._brain_thread.deleteLater)
        self._brain_thread.finished.connect(self._on_brain_complete)
        self._brain_thread.start()

    def _handle_response(self, response: str):
        if response:
            self._set_subtitle("Jarvis", response)
            self.set_avatar_state("speaking")
            error = speak_text(response)
            if error:
                self._set_subtitle("Jarvis", error)
            QTimer.singleShot(1800, lambda: self.set_avatar_state("idle"))
        else:
            self.set_avatar_state("idle")

    def _on_brain_complete(self):
        self._brain_thread = None
        self._brain_worker = None
        if self._listen_thread is None:
            self._set_inputs_enabled(True)
