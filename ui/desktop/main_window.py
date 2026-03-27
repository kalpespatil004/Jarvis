from __future__ import annotations

import time
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, Qt, QUrl, pyqtSignal
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

DEFAULT_AVATAR_DIR_CANDIDATES = ("avatar", "avtar")
DEFAULT_VIDEO_NAME_CANDIDATES = {
    "idle": ["idle.mp4", "ideal.mp4"],
    "listening": ["listening.mp4", "listnimg.mp4"],
    "thinking": ["thinking.mp4"],
    "speaking": ["speaking.mp4"],
}


class CycleWorker(QObject):
    state_changed = pyqtSignal(str)
    subtitle_changed = pyqtSignal(str, str)
    completed = pyqtSignal()

    def __init__(self, mode: str, text: str = ""):
        super().__init__()
        self.mode = mode
        self.text = text

    def run(self):
        try:
            self._process_cycle()
        finally:
            self.completed.emit()

    def _process_cycle(self):
        user_text = self.text.strip()

        if self.mode == "voice":
            self.state_changed.emit("listening")
            self.subtitle_changed.emit("Jarvis", "Listening...")
            try:
                user_text = capture_voice_text()
            except VoiceInputError as exc:
                self.subtitle_changed.emit("Jarvis", f"Listen error: {exc}")
                self.state_changed.emit("idle")
                return

        if not user_text:
            self.state_changed.emit("idle")
            return

        self.subtitle_changed.emit("You", user_text)
        self.state_changed.emit("thinking")

        response = process_text(user_text)
        if not response:
            self.subtitle_changed.emit("Jarvis", "I could not generate a response.")
            self.state_changed.emit("idle")
            return

        self.subtitle_changed.emit("Jarvis", response)
        self.state_changed.emit("speaking")
        error = speak_text(response)
        if error:
            self.subtitle_changed.emit("Jarvis", error)

        self.state_changed.emit("idle")

# =========================
# MAIN UI
# =========================

class MainWindow(QWidget):
    state_signal = pyqtSignal(str)
    subtitle_signal = pyqtSignal(str, str)

    AVATAR_DIR_CANDIDATES = DEFAULT_AVATAR_DIR_CANDIDATES
    VIDEO_NAME_CANDIDATES = DEFAULT_VIDEO_NAME_CANDIDATES

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")

        self._cycle_thread: QThread | None = None
        self._cycle_worker: CycleWorker | None = None

        self.avatar_state = "idle"
        self.video_paths = self._resolve_video_paths()
        self.players: dict[str, QMediaPlayer] = {}
        self._current_player: QMediaPlayer | None = None

        self.video_widget = QVideoWidget(self)

        self.init_ui()
        self.state_signal.connect(self.set_avatar_state)
        self.subtitle_signal.connect(self._set_subtitle)

        self._init_players()
        self._apply_video_geometry_hint()
        self.set_avatar_state("idle")

    def _resolve_video_paths(self) -> dict[str, Path]:
        project_root = Path(__file__).resolve().parents[2]
        avatar_dirs = getattr(self, "AVATAR_DIR_CANDIDATES", DEFAULT_AVATAR_DIR_CANDIDATES)
        video_candidates = getattr(self, "VIDEO_NAME_CANDIDATES", DEFAULT_VIDEO_NAME_CANDIDATES)
        search_dirs = [project_root / "assets" / name for name in avatar_dirs]
        resolved: dict[str, Path] = {}

        for state, candidates in video_candidates.items():
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

    def _make_player(self, source: Path, state: str) -> QMediaPlayer:
        player = QMediaPlayer(self)
        player.setSource(QUrl.fromLocalFile(str(source)))
        if hasattr(player, "setLoops"):
            player.setLoops(-1)

        def _status_handler(status: QMediaPlayer.MediaStatus):
            if status == QMediaPlayer.MediaStatus.EndOfMedia and not hasattr(player, "setLoops"):
                if player.isSeekable():
                    player.setPosition(0)
                    player.play()

        def _error_handler(_error):
            message = player.errorString() or "Unable to render avatar video."
            self.subtitle_signal.emit("Jarvis", f"Video error [{state}]: {message}")

        player.mediaStatusChanged.connect(_status_handler)
        player.errorOccurred.connect(_error_handler)
        return player

    def _init_players(self):
        idle_source = self.video_paths.get("idle")
        if idle_source is None:
            return

        video_candidates = getattr(self, "VIDEO_NAME_CANDIDATES", DEFAULT_VIDEO_NAME_CANDIDATES)
        for state in video_candidates:
            source = self.video_paths.get(state, idle_source)
            self.players[state] = self._make_player(source, state)

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

        self._subtitle_overlay.setGeometry(self.video_widget.geometry())
        margin_x = 16
        bottom_margin = 14
        width = max(200, self._subtitle_overlay.width() - margin_x * 2)
        height = max(56, self.subtitle_label.sizeHint().height())
        x = margin_x
        y = max(0, self._subtitle_overlay.height() - height - bottom_margin)
        self.subtitle_label.setGeometry(x, y, width, height)
        self.subtitle_label.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_subtitle()

    def _set_inputs_enabled(self, enabled: bool):
        self.send_btn.setDisabled(not enabled)
        self.listen_btn.setDisabled(not enabled)
        self.input_box.setDisabled(not enabled)
        if enabled:
            self.input_box.setFocus()

    def _set_subtitle(self, speaker: str, text: str):
        self.subtitle_label.setText(f"{speaker}: {text}")
        self.subtitle_label.adjustSize()
        self._layout_subtitle()

    def set_avatar_state(self, state: str):
        if self.avatar_state == state:
            return

        player = self.players.get(state) or self.players.get("idle")
        if player is None:
            search_hint = ", ".join(str(p) for p in self._avatar_search_dirs)
            self._set_subtitle("Jarvis", f"Avatar videos not found. Checked: {search_hint}")
            return

        self.avatar_state = state

        if self._current_player is not None and self._current_player is not player:
            self._current_player.stop()
            self._current_player.setVideoOutput(None)

        self._current_player = player
        player.setVideoOutput(self.video_widget)
        player.play()

    def _start_cycle(self, mode: str, text: str = ""):
        if self._cycle_thread is not None:
            return

        self._set_inputs_enabled(False)

        self._cycle_thread = QThread(self)
        self._cycle_worker = CycleWorker(mode=mode, text=text)
        self._cycle_worker.moveToThread(self._cycle_thread)

        self._cycle_thread.started.connect(self._cycle_worker.run)
        self._cycle_worker.state_changed.connect(self.state_signal.emit)
        self._cycle_worker.subtitle_changed.connect(self.subtitle_signal.emit)
        self._cycle_worker.completed.connect(self._cycle_thread.quit)
        self._cycle_worker.completed.connect(self._cycle_worker.deleteLater)
        self._cycle_thread.finished.connect(self._cycle_thread.deleteLater)
        self._cycle_thread.finished.connect(self._on_cycle_complete)

        self._cycle_thread.start()

    def _on_cycle_complete(self):
        self._cycle_thread = None
        self._cycle_worker = None
        self._set_inputs_enabled(True)

    def listen_once(self):
        self._start_cycle("voice")

    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return

        self.input_box.clear()
        self._start_cycle("text", text)
