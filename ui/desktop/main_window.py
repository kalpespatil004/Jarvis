from __future__ import annotations

import time
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QPalette
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from brain.brain import process_text
from ui.desktop.tts_bridge import speak_text
from ui.desktop.voice_input import VoiceInputError, capture_voice_text


# =========================
# WORKERS
# =========================

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


# =========================
# MAIN UI
# =========================

class MainWindow(QWidget):

    VIDEO_NAME = {
        "idle": "idle.mp4",
        "listening": "listening.mp4",
        "thinking": "thinking.mp4",
        "speaking": "speaking.mp4",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")

        self.avatar_state = None
        self._current_video = None

        self._brain_thread = None
        self._listen_thread = None

        self.video_paths = self._load_videos()

        # ===== PLAYER =====
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0)

        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio)

        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        self.player.mediaStatusChanged.connect(self._loop_video)

        # ===== TIMER =====
        self.idle_timer = QTimer(self)
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(lambda: self.set_state("idle"))

        self.init_ui()
        self.set_state("idle")

    # =========================
    # LOAD VIDEOS
    # =========================

    def _load_videos(self):
        base = Path(__file__).resolve().parents[2] / "assets" / "avatar"
        paths = {}

        for k, v in self.VIDEO_NAME.items():
            p = base / v
            if p.exists():
                paths[k] = p

        return paths

    # =========================
    # UI
    # =========================

    def init_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        stack = QStackedLayout(container)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        stack.addWidget(self.video_widget)

        # subtitle
        self.subtitle = QLabel("Jarvis: Online")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("""
            background: rgba(0,0,0,180);
            color: white;
            padding: 10px;
            font-size: 16px;
            border-radius: 10px;
        """)

        stack.addWidget(self.subtitle)

        # controls
        controls = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type command...")
        self.input.returnPressed.connect(self.send)

        self.listen_btn = QPushButton("Listen")
        self.listen_btn.clicked.connect(self.listen)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send)

        controls.addWidget(self.input)
        controls.addWidget(self.listen_btn)
        controls.addWidget(self.send_btn)

        root.addWidget(container)
        root.addLayout(controls)

        self.setLayout(root)
        self.resize(500, 800)

    # =========================
    # STATE CONTROL (IMPORTANT)
    # =========================

    def set_state(self, state: str):
        if state == self.avatar_state:
            return

        self.avatar_state = state

        source = self.video_paths.get(state) or self.video_paths.get("idle")
        if not source:
            return

        if self._current_video != source:
            self._current_video = source
            self.player.setSource(QUrl.fromLocalFile(str(source)))
            self.player.play()

    def _loop_video(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    # =========================
    # SUBTITLE
    # =========================

    def set_subtitle(self, speaker, text):
        self.subtitle.setText(f"{speaker}: {text}")

    # =========================
    # LISTEN
    # =========================

    def listen(self):
        if self._listen_thread:
            return

        self.set_state("listening")
        self.set_subtitle("Jarvis", "Listening...")

        self._listen_thread = QThread()
        worker = ListenWorker()
        worker.moveToThread(self._listen_thread)

        self._listen_thread.started.connect(worker.run)
        worker.success.connect(self.on_listen_success)
        worker.error.connect(self.on_listen_error)

        worker.success.connect(self._listen_thread.quit)
        worker.error.connect(self._listen_thread.quit)

        self._listen_thread.finished.connect(lambda: setattr(self, "_listen_thread", None))

        self._listen_thread.start()

    def on_listen_success(self, text):
        self.input.setText(text)
        self.set_subtitle("You", text)

        # small delay so animation shows
        QTimer.singleShot(500, self.send)

    def on_listen_error(self, err):
        self.set_subtitle("Jarvis", err)
        self.set_state("idle")

    # =========================
    # SEND
    # =========================

    def send(self):
        text = self.input.text().strip()
        if not text or self._brain_thread:
            return

        self.input.clear()

        self.set_subtitle("You", text)
        self.set_state("thinking")

        self._brain_thread = QThread()
        worker = BrainWorker(text)
        worker.moveToThread(self._brain_thread)

        self._brain_thread.started.connect(worker.run)
        worker.finished.connect(self.on_response)

        worker.finished.connect(self._brain_thread.quit)
        self._brain_thread.finished.connect(lambda: setattr(self, "_brain_thread", None))

        self._brain_thread.start()

    # =========================
    # RESPONSE
    # =========================

    def on_response(self, response):
        if not response:
            self.set_state("idle")
            return

        self.set_subtitle("Jarvis", response)
        self.set_state("speaking")

        speak_text(response)

        # 🔥 dynamic speaking duration
        duration = max(1500, len(response) * 60)
        self.idle_timer.start(duration)