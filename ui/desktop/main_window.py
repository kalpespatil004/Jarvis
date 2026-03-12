from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QPalette
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
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
        "idle": ["idle.mp4", "ideal.mp4"],
        "listening": ["listening.mp4", "listnimg.mp4"],
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
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        # Loop current state video forever.
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

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

        video_container = QWidget(self)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(0)
        video_layout.addWidget(self.video_widget)

        self.subtitle_label = QLabel("Jarvis: Online.", video_container)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 160);
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 18px;
                font-weight: 600;
            }
            """
        )
        self.subtitle_label.setMinimumHeight(56)

        # Keep subtitles near bottom over video.
        video_layout.addStretch(1)
        video_layout.addWidget(self.subtitle_label)
        video_layout.setAlignment(self.subtitle_label, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

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

        root.addWidget(video_container, 1)
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

        palette = self.video_widget.palette()
        palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.black)
        self.video_widget.setPalette(palette)
        self.video_widget.setAutoFillBackground(True)

    def _set_inputs_enabled(self, enabled: bool):
        self.send_btn.setDisabled(not enabled)
        self.listen_btn.setDisabled(not enabled)
        self.input_box.setDisabled(not enabled)
        if enabled:
            self.input_box.setFocus()

    def _set_subtitle(self, speaker: str, text: str):
        self.subtitle_label.setText(f"{speaker}: {text}")

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
