from __future__ import annotations

import threading
import time
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
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
from ui.desktop.voice_input import (
    VoiceInputError,
    capture_command_text,
    extract_inline_command,
    listen_for_wake_word,
)

DEFAULT_AVATAR_DIR_CANDIDATES = ("avatar", "avtar")
DEFAULT_VIDEO_NAME_CANDIDATES = {
    "idle": ["idle.mp4", "ideal.mp4"],
    "listening": ["listening.mp4", "listnimg.mp4"],
    "thinking": ["thinking.mp4"],
    "speaking": ["speaking.mp4"],
}

STATE_LABELS = {
    "idle": "Idle",
    "wake_listening": "Wake Listening",
    "command_listening": "Listening",
    "thinking": "Thinking",
    "speaking": "Speaking",
}

AVATAR_STATE_MAP = {
    "wake_listening": "listening",
    "command_listening": "listening",
}

WAKE_HINT = "Wake mode on. Say 'hey jarvis', 'wake up', or 'jarvis'."
WAKE_REARM_DELAY_SECONDS = 1.2


class CommandWorker(QObject):
    state_changed = pyqtSignal(str)
    subtitle_changed = pyqtSignal(str, str)
    completed = pyqtSignal()

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        try:
            self._process_command()
        finally:
            self.completed.emit()

    def _process_command(self):
        user_text = self.text.strip()
        if not user_text:
            return

        self.subtitle_changed.emit("You", user_text)
        self.state_changed.emit("thinking")

        response = process_text(user_text)
        if not response:
            self.subtitle_changed.emit("Jarvis", "I could not generate a response.")
            return

        self.subtitle_changed.emit("Jarvis", response)
        self.state_changed.emit("speaking")
        error = speak_text(response)
        if error:
            self.subtitle_changed.emit("Jarvis", error)
            return

        time.sleep(self._estimate_speaking_delay(response))

    @staticmethod
    def _estimate_speaking_delay(text: str) -> float:
        word_count = max(1, len(text.split()))
        return max(1.2, min(word_count * 0.28, 6.0))


class WakeWordWorker(QObject):
    state_changed = pyqtSignal(str)
    subtitle_changed = pyqtSignal(str, str)
    command_captured = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self._resume_event = threading.Event()
        self._resume_event.set()
        self._listen_stop_event = threading.Event()
        self._next_ready_at = 0.0

    def run(self):
        try:
            while not self._stop_event.is_set():
                if not self._resume_event.wait(timeout=0.1):
                    continue

                remaining_cooldown = self._next_ready_at - time.monotonic()
                if remaining_cooldown > 0:
                    time.sleep(min(remaining_cooldown, 0.2))
                    continue

                self._listen_stop_event.clear()
                self.state_changed.emit("wake_listening")
                self.subtitle_changed.emit("Jarvis", WAKE_HINT)

                try:
                    wake_text = listen_for_wake_word(stop_event=self._listen_stop_event)
                except VoiceInputError as exc:
                    if self._stop_event.is_set():
                        break
                    self.subtitle_changed.emit("Jarvis", f"Wake listener error: {exc}")
                    time.sleep(0.5)
                    continue

                if self._stop_event.is_set():
                    break

                if not self._resume_event.is_set():
                    continue

                if not wake_text:
                    continue

                self._next_ready_at = time.monotonic() + WAKE_REARM_DELAY_SECONDS
                self.state_changed.emit("command_listening")
                inline_command = extract_inline_command(wake_text)
                if inline_command:
                    self.subtitle_changed.emit("Jarvis", f"Heard '{wake_text}'. Processing your command.")
                    command_text = inline_command
                else:
                    self.subtitle_changed.emit("Jarvis", f"Heard '{wake_text}'. I am listening.")
                    print(f"[WAKE] Detected '{wake_text}'. Listening for command...")
                    time.sleep(0.35)

                    try:
                        command_text = capture_command_text()
                    except VoiceInputError as exc:
                        self.subtitle_changed.emit("Jarvis", f"Listen error: {exc}")
                        continue

                if not command_text:
                    self.subtitle_changed.emit("Jarvis", "No command heard. Say the wake word again.")
                    continue

                self._resume_event.clear()
                self.command_captured.emit(command_text)

                while not self._stop_event.is_set() and not self._resume_event.wait(timeout=0.1):
                    pass
        finally:
            self.finished.emit()

    def pause(self):
        self._resume_event.clear()
        self._listen_stop_event.set()

    def resume_listening(self):
        self._listen_stop_event.clear()
        self._resume_event.set()
        self._next_ready_at = max(self._next_ready_at, time.monotonic() + WAKE_REARM_DELAY_SECONDS)

    def stop(self):
        self._stop_event.set()
        self._listen_stop_event.set()
        self._resume_event.set()


class MainWindow(QWidget):
    state_signal = pyqtSignal(str)
    subtitle_signal = pyqtSignal(str, str)

    AVATAR_DIR_CANDIDATES = DEFAULT_AVATAR_DIR_CANDIDATES
    VIDEO_NAME_CANDIDATES = DEFAULT_VIDEO_NAME_CANDIDATES

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")

        self._command_thread: QThread | None = None
        self._command_worker: CommandWorker | None = None
        self._return_to_wake_after_command = False

        self._wake_thread: QThread | None = None
        self._wake_worker: WakeWordWorker | None = None
        self._wake_mode_enabled = False

        self.avatar_state = "idle"
        self.video_paths = self._resolve_video_paths()
        self._current_video_source: Path | None = None

        self._audio_output = QAudioOutput(self)
        self._audio_output.setVolume(0.0)

        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self._audio_output)

        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_player_error)

        self.init_ui()
        self.state_signal.connect(self.set_avatar_state)
        self.subtitle_signal.connect(self._set_subtitle)

        self._apply_video_geometry_hint()
        self.set_avatar_state("idle")
        self._set_subtitle("Jarvis", "Online. Click Listen once to enable wake mode.")

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

    def _apply_video_geometry_hint(self):
        try:
            import cv2  # type: ignore

            probe = self.video_paths.get("idle") or next(iter(self.video_paths.values()))
            cap = cv2.VideoCapture(str(probe))
            ok, frame = cap.read()
            cap.release()
            if ok and frame is not None:
                height, width = frame.shape[:2]
                self.setFixedSize(width, height + 72)
                return
        except Exception:
            pass

        self.setFixedSize(560, 912)

    def init_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        video_container = QWidget(self)
        stacked = QStackedLayout(video_container)
        stacked.setStackingMode(QStackedLayout.StackingMode.StackAll)
        stacked.setContentsMargins(0, 0, 0, 0)

        self.video_widget.setStyleSheet("background: black;")
        stacked.addWidget(self.video_widget)

        self._overlay = QWidget(video_container)
        self._overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._overlay.setStyleSheet("background: transparent;")
        stacked.addWidget(self._overlay)

        overlay_layout = QVBoxLayout(self._overlay)
        overlay_layout.setContentsMargins(16, 16, 16, 14)
        overlay_layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.state_badge = QLabel("State: Idle", self._overlay)
        self.state_badge.setStyleSheet(
            """
            QLabel {
                color: #f5f7fb;
                background-color: rgba(0, 0, 0, 185);
                border: 1px solid rgba(255, 255, 255, 75);
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 700;
            }
            """
        )
        top_row.addWidget(self.state_badge, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_row.addStretch(1)
        overlay_layout.addLayout(top_row)
        overlay_layout.addStretch(1)

        self.subtitle_label = QLabel("Jarvis: Online.", self._overlay)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 190);
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 18px;
                font-weight: 600;
            }
            """
        )
        self.subtitle_label.setMinimumHeight(56)
        overlay_layout.addWidget(self.subtitle_label, 0, Qt.AlignmentFlag.AlignBottom)

        controls = QWidget(self)
        controls.setFixedHeight(72)
        controls.setObjectName("controlsPanel")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(10, 8, 10, 8)
        controls_layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type a command...")
        self.input_box.returnPressed.connect(self.send_message)
        self.input = self.input_box

        self.listen_btn = QPushButton("Listen")
        self.listen_btn.clicked.connect(self.listen_once)
        self.listen = self.listen_once

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_button = self.send_btn

        controls_layout.addWidget(self.input_box, 1)
        controls_layout.addWidget(self.listen_btn)
        controls_layout.addWidget(self.send_btn)

        root.addWidget(video_container, 1)
        root.addWidget(controls, 0)
        self.setLayout(root)
        self.resize(560, 912)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._overlay.raise_()
        self.state_badge.raise_()
        self.subtitle_label.raise_()

    def closeEvent(self, event: QCloseEvent):
        self._stop_wake_loop()
        super().closeEvent(event)

    def _set_subtitle(self, speaker: str, text: str):
        self.subtitle_label.setText(f"{speaker}: {text}")
        self.subtitle_label.adjustSize()

    def _update_state_badge(self, state: str):
        label = STATE_LABELS.get(state, state.title())
        self.state_badge.setText(f"State: {label}")
        self.state_badge.adjustSize()
        self.state_badge.raise_()

    def set_avatar_state(self, state: str):
        avatar_state = AVATAR_STATE_MAP.get(state, state)
        source = self.video_paths.get(avatar_state) or self.video_paths.get("idle")

        self.avatar_state = state
        self._update_state_badge(state)

        if source is None:
            search_hint = ", ".join(str(p) for p in self._avatar_search_dirs)
            self._set_subtitle("Jarvis", f"Avatar videos not found. Checked: {search_hint}")
            return

        if self._current_video_source == source:
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.player.play()
            return

        self._current_video_source = source
        self.player.setSource(QUrl.fromLocalFile(str(source)))
        self.player.play()

    def set_state(self, state: str):
        self.set_avatar_state(state)

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.player.isSeekable():
            self.player.setPosition(0)
            self.player.play()

    def _on_player_error(self, _error):
        message = self.player.errorString() or "Unable to render avatar video."
        self._set_subtitle("Jarvis", f"Video error: {message}")

    def _set_inputs_busy(self, busy: bool):
        self.send_btn.setDisabled(busy)
        self.input_box.setDisabled(busy)
        self.listen_btn.setDisabled(busy and not self._wake_mode_enabled)
        if not busy:
            self.input_box.setFocus()

    def _update_listen_button(self):
        self.listen_btn.setText("Wake On" if self._wake_mode_enabled else "Listen")
        self.listen_btn.setDisabled(False)

    def _ensure_wake_loop(self):
        if self._wake_thread is not None:
            return

        self._wake_worker = WakeWordWorker()
        self._wake_thread = QThread(self)
        self._wake_worker.moveToThread(self._wake_thread)

        self._wake_thread.started.connect(self._wake_worker.run)
        self._wake_worker.state_changed.connect(self.state_signal.emit)
        self._wake_worker.subtitle_changed.connect(self.subtitle_signal.emit)
        self._wake_worker.command_captured.connect(self._on_wake_command_captured)
        self._wake_worker.finished.connect(self._wake_thread.quit)
        self._wake_worker.finished.connect(self._wake_worker.deleteLater)
        self._wake_thread.finished.connect(self._wake_thread.deleteLater)
        self._wake_thread.finished.connect(self._on_wake_thread_finished)
        self._wake_thread.start()

    def _stop_wake_loop(self):
        if self._wake_worker is not None:
            self._wake_worker.stop()
        if self._wake_thread is not None:
            self._wake_thread.quit()
            self._wake_thread.wait(2000)
        self._wake_mode_enabled = False
        self._update_listen_button()

    def _on_wake_thread_finished(self):
        self._wake_thread = None
        self._wake_worker = None
        self._wake_mode_enabled = False
        self._update_listen_button()
        if self._command_thread is None:
            self.set_avatar_state("idle")

    def _pause_wake_loop(self):
        if self._wake_worker is not None:
            self._wake_worker.pause()

    def _resume_wake_loop(self):
        if self._wake_worker is not None and self._wake_mode_enabled:
            self._wake_worker.resume_listening()

    def _start_command_cycle(self, text: str, return_to_wake: bool):
        if self._command_thread is not None:
            return

        self._return_to_wake_after_command = return_to_wake
        if return_to_wake:
            self._pause_wake_loop()

        self._set_inputs_busy(True)

        self._command_thread = QThread(self)
        self._command_worker = CommandWorker(text)
        self._command_worker.moveToThread(self._command_thread)

        self._command_thread.started.connect(self._command_worker.run)
        self._command_worker.state_changed.connect(self.state_signal.emit)
        self._command_worker.subtitle_changed.connect(self.subtitle_signal.emit)
        self._command_worker.completed.connect(self._command_thread.quit)
        self._command_worker.completed.connect(self._command_worker.deleteLater)
        self._command_thread.finished.connect(self._command_thread.deleteLater)
        self._command_thread.finished.connect(self._on_command_complete)

        self._command_thread.start()

    def _on_command_complete(self):
        self._command_thread = None
        self._command_worker = None
        self._set_inputs_busy(False)

        if self._return_to_wake_after_command and self._wake_mode_enabled:
            self._resume_wake_loop()
        else:
            self.set_avatar_state("idle")

        self._return_to_wake_after_command = False

    def _on_wake_command_captured(self, text: str):
        self._start_command_cycle(text, return_to_wake=True)

    def listen_once(self):
        if self._wake_mode_enabled:
            self._set_subtitle("Jarvis", WAKE_HINT)
            self.set_avatar_state("wake_listening")
            return

        self._wake_mode_enabled = True
        self._update_listen_button()
        self._ensure_wake_loop()
        self.set_avatar_state("wake_listening")
        self._set_subtitle("Jarvis", WAKE_HINT)

    def send(self):
        self.send_message()

    def send_message(self):
        text = self.input_box.text().strip()
        if not text or self._command_thread is not None:
            return

        self.input_box.clear()
        self._start_command_cycle(text, return_to_wake=self._wake_mode_enabled)
