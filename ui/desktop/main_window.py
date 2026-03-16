"""
ui/desktop/main_window.py
--------------------------
Jarvis Desktop GUI — Full Iron Man–style dark UI.

Features:
• Animated avatar (video states: idle / listening / speaking / thinking)
• Chat message window with Jarvis/User bubbles
• Voice input button (hold to speak or click to toggle)
• Text input bar
• Sidebar (Services panel: weather, news, crypto, system info)
• Settings panel
• Status bar
"""

import os
import sys
import threading

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea,
    QFrame, QSizePolicy, QTextEdit, QSplitter,
    QStackedWidget, QApplication, QGraphicsDropShadowEffect,
    QToolButton
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, QRect, pyqtSlot
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPixmap, QIcon,
    QTextCursor, QLinearGradient, QPainter
)

try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    _VIDEO_AVAILABLE = True
except ImportError:
    _VIDEO_AVAILABLE = False

try:
    from utils.constants import (
        JARVIS_BLUE, JARVIS_DARK, JARVIS_DARK2, JARVIS_ACCENT,
        JARVIS_GREEN, JARVIS_TEXT, JARVIS_SUBTEXT
    )
except ImportError:
    JARVIS_BLUE    = "#00BFFF"
    JARVIS_DARK    = "#0a0a1a"
    JARVIS_DARK2   = "#0f0f2e"
    JARVIS_ACCENT  = "#1a1a3e"
    JARVIS_GREEN   = "#00ff88"
    JARVIS_TEXT    = "#e0e0ff"
    JARVIS_SUBTEXT = "#8888aa"


# ═══════════════════════════════════════════════════════════════
# WORKER THREADS
# ═══════════════════════════════════════════════════════════════

class BrainWorker(QThread):
    """Background thread: processes user input and emits response."""
    response_ready   = pyqtSignal(str)
    state_changed    = pyqtSignal(str)   # "idle" | "thinking" | "speaking"

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        self.state_changed.emit("thinking")
        try:
            from brain.brain import process_text
            reply = process_text(self.text)
        except Exception as e:
            reply = f"Error: {e}"
        self.response_ready.emit(reply or "I didn't quite get that.")
        self.state_changed.emit("speaking")


class VoiceWorker(QThread):
    """Background thread: listens for voice input."""
    heard    = pyqtSignal(str)
    listening= pyqtSignal(bool)

    def run(self):
        self.listening.emit(True)
        try:
            from body.listen import listen
            text = listen(timeout=10)
            if text:
                self.heard.emit(text)
        except Exception as e:
            print(f"[Voice] Error: {e}")
        finally:
            self.listening.emit(False)


# ═══════════════════════════════════════════════════════════════
# CHAT BUBBLE WIDGET
# ═══════════════════════════════════════════════════════════════

class ChatBubble(QFrame):
    def __init__(self, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self._build(text)

    def _build(self, text: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        label.setFont(QFont("Segoe UI", 10))
        label.setMaximumWidth(520)

        if self.is_user:
            label.setStyleSheet(f"""
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a3a6e, stop:1 #0d2040
                );
                color: {JARVIS_TEXT};
                border-radius: 14px;
                padding: 10px 14px;
                border: 1px solid #2a5a9e;
            """)
            layout.addStretch()
            layout.addWidget(label)
        else:
            label.setStyleSheet(f"""
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f1f40, stop:1 #0d1830
                );
                color: {JARVIS_BLUE};
                border-radius: 14px;
                padding: 10px 14px;
                border: 1px solid #00406a;
            """)
            layout.addWidget(label)
            layout.addStretch()

        self.setStyleSheet("background: transparent; border: none;")


# ═══════════════════════════════════════════════════════════════
# AVATAR WIDGET
# ═══════════════════════════════════════════════════════════════

class AvatarWidget(QWidget):
    """Shows animated avatar based on Jarvis state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._state = "idle"
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # State label (text indicator when video not available)
        self._state_icons = {
            "idle"     : "💤",
            "listening": "👂",
            "thinking" : "🤔",
            "speaking" : "🗣️",
        }

        if _VIDEO_AVAILABLE:
            self._video_widget = QVideoWidget()
            self._player       = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._player.setVideoOutput(self._video_widget)
            self._layout.addWidget(self._video_widget)
        else:
            self._label = QLabel("🤖")
            self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._label.setFont(QFont("Segoe UI Emoji", 80))
            self._label.setStyleSheet(f"color: {JARVIS_BLUE}; background: transparent;")
            self._layout.addWidget(self._label)

        # State label below
        self._state_label = QLabel("ONLINE")
        self._state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        self._state_label.setStyleSheet(f"color: {JARVIS_GREEN}; background: transparent;")
        self._layout.addWidget(self._state_label)

        self.setStyleSheet(f"""
            background: qradialgradient(
                cx:0.5, cy:0.5, radius:0.5,
                stop:0 #0a1535, stop:1 {JARVIS_DARK}
            );
            border-radius: 110px;
            border: 2px solid {JARVIS_BLUE};
        """)

    def set_state(self, state: str):
        self._state = state
        self._state_label.setText(state.upper())

        color_map = {
            "idle"     : JARVIS_SUBTEXT,
            "listening": JARVIS_GREEN,
            "thinking" : "#FFD700",
            "speaking" : JARVIS_BLUE,
        }
        c = color_map.get(state, JARVIS_BLUE)
        self._state_label.setStyleSheet(f"color: {c}; background: transparent;")

        if _VIDEO_AVAILABLE:
            try:
                from config import AVATAR_DIR
                from PyQt6.QtCore import QUrl
                path = os.path.join(AVATAR_DIR, f"{state}.mp4")
                if os.path.exists(path):
                    self._player.setSource(QUrl.fromLocalFile(path))
                    self._player.setLoops(QMediaPlayer.Loops.Infinite)  # type: ignore
                    self._player.play()
            except Exception:
                pass

        if not _VIDEO_AVAILABLE:
            icon = self._state_icons.get(state, "🤖")
            self._label.setText(icon)  # type: ignore


# ═══════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S — Just A Rather Very Intelligent System")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self._voice_worker   = None
        self._brain_workers  = []
        self._speaking_timer = QTimer()
        self._speaking_timer.setSingleShot(True)
        self._speaking_timer.timeout.connect(self._on_speaking_done)

        self._build_ui()
        self._apply_global_style()
        self._greet()

    # ─── BUILD UI ────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left sidebar
        self._sidebar = self._build_sidebar()
        root.addWidget(self._sidebar)

        # Main panel (avatar + chat)
        main_panel = self._build_main_panel()
        root.addWidget(main_panel, stretch=1)

        # Status bar
        self.statusBar().setStyleSheet(f"""
            background: {JARVIS_DARK};
            color: {JARVIS_SUBTEXT};
            font-family: 'Courier New'; font-size: 9px;
        """)
        self.statusBar().showMessage("JARVIS v2.0  |  Ready")

    # ─── SIDEBAR ─────────────────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {JARVIS_DARK2};
                border-right: 1px solid #0a2040;
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        # Logo
        logo = QLabel("J.A.R.V.I.S")
        logo.setFont(QFont("Courier New", 16, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {JARVIS_BLUE}; letter-spacing: 3px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        sub = QLabel("AI Assistant v2.0")
        sub.setFont(QFont("Segoe UI", 8))
        sub.setStyleSheet(f"color: {JARVIS_SUBTEXT};")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(20)

        # Quick-action buttons
        actions = [
            ("🌤  Weather",       "get weather in my city"),
            ("📰  News",          "get latest news"),
            ("💰  Bitcoin Price", "bitcoin price in inr"),
            ("⏰  Time",          "what time is it"),
            ("📅  Date",          "what is today's date"),
            ("💻  System Info",   "system info"),
            ("📸  Screenshot",    "take a screenshot"),
        ]

        for label, command in actions:
            btn = QPushButton(label)
            btn.setFont(QFont("Segoe UI", 9))
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {JARVIS_ACCENT};
                    color: {JARVIS_TEXT};
                    border: 1px solid #1a3060;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 10px;
                }}
                QPushButton:hover {{
                    background: #1e2a50;
                    border: 1px solid {JARVIS_BLUE};
                    color: {JARVIS_BLUE};
                }}
                QPushButton:pressed {{
                    background: #0d1830;
                }}
            """)
            btn.clicked.connect(lambda _, c=command: self._send_text(c))
            layout.addWidget(btn)

        layout.addStretch()

        # Version info
        ver = QLabel("Build 2025.03.16")
        ver.setFont(QFont("Courier New", 7))
        ver.setStyleSheet(f"color: {JARVIS_SUBTEXT};")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        return sidebar

    # ─── MAIN PANEL ──────────────────────────────────────────
    def _build_main_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        top_bar = self._build_top_bar()
        layout.addWidget(top_bar)

        # Content area (avatar left, chat right)
        content = QSplitter(Qt.Orientation.Horizontal)
        content.setStyleSheet("QSplitter::handle { background: #0a2040; width: 1px; }")

        # Avatar panel
        avatar_panel = self._build_avatar_panel()
        content.addWidget(avatar_panel)
        content.setStretchFactor(0, 0)

        # Chat panel
        chat_panel = self._build_chat_panel()
        content.addWidget(chat_panel)
        content.setStretchFactor(1, 1)

        content.setSizes([260, 820])
        layout.addWidget(content, stretch=1)

        # Input bar
        input_bar = self._build_input_bar()
        layout.addWidget(input_bar)

        return panel

    # ─── TOP BAR ─────────────────────────────────────────────
    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {JARVIS_DARK2};
                border-bottom: 1px solid #0a2040;
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)

        # Status indicator
        self._status_dot = QLabel("●")
        self._status_dot.setFont(QFont("Segoe UI", 14))
        self._status_dot.setStyleSheet(f"color: {JARVIS_GREEN};")
        layout.addWidget(self._status_dot)

        self._status_text = QLabel("SYSTEMS ONLINE")
        self._status_text.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._status_text.setStyleSheet(f"color: {JARVIS_BLUE}; letter-spacing: 2px;")
        layout.addWidget(self._status_text)

        layout.addStretch()

        # Clear chat button
        clear_btn = QPushButton("🗑  Clear Chat")
        clear_btn.setFixedHeight(28)
        clear_btn.setFont(QFont("Segoe UI", 8))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {JARVIS_SUBTEXT};
                border: 1px solid #1a2040;
                border-radius: 4px;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                color: {JARVIS_TEXT};
                border-color: {JARVIS_BLUE};
            }}
        """)
        clear_btn.clicked.connect(self._clear_chat)
        layout.addWidget(clear_btn)

        return bar

    # ─── AVATAR PANEL ────────────────────────────────────────
    def _build_avatar_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(260)
        panel.setStyleSheet(f"background: {JARVIS_DARK};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._avatar = AvatarWidget()
        layout.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(20)

        # Stats panel
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background: {JARVIS_DARK2};
                border: 1px solid #0a2040;
                border-radius: 8px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(12, 10, 12, 10)
        stats_layout.setSpacing(4)

        self._stats = {}
        for key, val in [("MODE", "UI"), ("LLM", "Gemini"), ("STT", "Vosk"), ("TTS", "Coqui")]:
            row = QHBoxLayout()
            k_label = QLabel(key)
            k_label.setFont(QFont("Courier New", 8))
            k_label.setStyleSheet(f"color: {JARVIS_SUBTEXT};")

            v_label = QLabel(val)
            v_label.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
            v_label.setStyleSheet(f"color: {JARVIS_BLUE};")
            v_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            row.addWidget(k_label)
            row.addStretch()
            row.addWidget(v_label)
            stats_layout.addLayout(row)
            self._stats[key] = v_label

        layout.addWidget(stats_frame)
        layout.addStretch()

        return panel

    # ─── CHAT PANEL ──────────────────────────────────────────
    def _build_chat_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {JARVIS_DARK};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Chat header
        header = QLabel("  💬  CONVERSATION")
        header.setFixedHeight(32)
        header.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        header.setStyleSheet(f"""
            color: {JARVIS_SUBTEXT};
            background: {JARVIS_DARK2};
            border-bottom: 1px solid #0a2040;
            padding-left: 12px;
            letter-spacing: 2px;
        """)
        layout.addWidget(header)

        # Scroll area for messages
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: {JARVIS_DARK};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {JARVIS_DARK2};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: #1a3060;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {JARVIS_BLUE};
            }}
        """)

        self._chat_container = QWidget()
        self._chat_container.setStyleSheet(f"background: {JARVIS_DARK};")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(16, 16, 16, 16)
        self._chat_layout.setSpacing(8)
        self._chat_layout.addStretch()

        self._scroll_area.setWidget(self._chat_container)
        layout.addWidget(self._scroll_area)

        return panel

    # ─── INPUT BAR ───────────────────────────────────────────
    def _build_input_bar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(72)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {JARVIS_DARK2};
                border-top: 1px solid #0a2040;
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Voice button
        self._voice_btn = QPushButton("🎙️")
        self._voice_btn.setFixedSize(46, 46)
        self._voice_btn.setFont(QFont("Segoe UI Emoji", 18))
        self._voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._voice_btn.setToolTip("Click to speak")
        self._voice_btn.setStyleSheet(f"""
            QPushButton {{
                background: {JARVIS_ACCENT};
                border: 2px solid #1a3060;
                border-radius: 23px;
                color: {JARVIS_BLUE};
            }}
            QPushButton:hover {{
                background: #1e2a50;
                border-color: {JARVIS_BLUE};
            }}
            QPushButton:pressed, QPushButton:checked {{
                background: #003366;
                border-color: {JARVIS_GREEN};
                color: {JARVIS_GREEN};
            }}
        """)
        self._voice_btn.setCheckable(True)
        self._voice_btn.clicked.connect(self._toggle_voice)
        layout.addWidget(self._voice_btn)

        # Text input
        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("  Type a command or ask anything...")
        self._text_input.setFont(QFont("Segoe UI", 11))
        self._text_input.setFixedHeight(46)
        self._text_input.setStyleSheet(f"""
            QLineEdit {{
                background: #0d1830;
                color: {JARVIS_TEXT};
                border: 2px solid #1a3060;
                border-radius: 23px;
                padding: 0 16px;
            }}
            QLineEdit:focus {{
                border-color: {JARVIS_BLUE};
                background: #0f1e3a;
            }}
            QLineEdit::placeholder {{
                color: {JARVIS_SUBTEXT};
            }}
        """)
        self._text_input.returnPressed.connect(self._on_send)
        layout.addWidget(self._text_input, stretch=1)

        # Send button
        self._send_btn = QPushButton("➤")
        self._send_btn.setFixedSize(46, 46)
        self._send_btn.setFont(QFont("Segoe UI", 18))
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0055aa, stop:1 #003388
                );
                border: 2px solid {JARVIS_BLUE};
                border-radius: 23px;
                color: white;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0077cc, stop:1 #0055aa
                );
            }}
            QPushButton:pressed {{
                background: #002266;
            }}
        """)
        self._send_btn.clicked.connect(self._on_send)
        layout.addWidget(self._send_btn)

        return bar

    # ─── GLOBAL STYLE ────────────────────────────────────────
    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {JARVIS_DARK};
            }}
            QToolTip {{
                background: {JARVIS_DARK2};
                color: {JARVIS_TEXT};
                border: 1px solid {JARVIS_BLUE};
                font-family: 'Segoe UI';
                font-size: 10px;
            }}
        """)

    # ─── GREETING ────────────────────────────────────────────
    def _greet(self):
        try:
            from config import USER_NAME
        except ImportError:
            USER_NAME = "Sir"
        self._add_jarvis_message(
            f"Good day, {USER_NAME}. All systems are online.\n"
            "I am ready to assist. How can I help you today?"
        )

    # ─── ACTIONS ─────────────────────────────────────────────
    def _on_send(self):
        text = self._text_input.text().strip()
        if not text:
            return
        self._text_input.clear()
        self._send_text(text)

    def _send_text(self, text: str):
        self._add_user_message(text)
        self._avatar.set_state("thinking")
        self._status_text.setText("PROCESSING...")
        self._text_input.setEnabled(False)
        self._send_btn.setEnabled(False)

        worker = BrainWorker(text)
        worker.response_ready.connect(self._on_response)
        worker.state_changed.connect(self._on_state_change)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._brain_workers.append(worker)
        worker.start()

    @pyqtSlot(str)
    def _on_response(self, reply: str):
        self._add_jarvis_message(reply)
        self._text_input.setEnabled(True)
        self._send_btn.setEnabled(True)
        self._text_input.setFocus()
        # Speak reply in background
        threading.Thread(
            target=self._speak_reply, args=(reply,), daemon=True
        ).start()

    def _speak_reply(self, text: str):
        try:
            from body.speak import speak
            speak(text)
        except Exception:
            pass
        QTimer.singleShot(3000, lambda: self._avatar.set_state("idle"))

    @pyqtSlot(str)
    def _on_state_change(self, state: str):
        self._avatar.set_state(state)
        labels = {
            "thinking": "PROCESSING...",
            "speaking": "RESPONDING...",
            "idle"    : "SYSTEMS ONLINE"
        }
        self._status_text.setText(labels.get(state, "SYSTEMS ONLINE"))

    def _on_speaking_done(self):
        self._avatar.set_state("idle")
        self._status_text.setText("SYSTEMS ONLINE")

    def _cleanup_worker(self, worker):
        if worker in self._brain_workers:
            self._brain_workers.remove(worker)

    # ─── VOICE ───────────────────────────────────────────────
    def _toggle_voice(self, checked: bool):
        if checked:
            self._start_listening()
        else:
            self._voice_btn.setChecked(False)

    def _start_listening(self):
        if self._voice_worker and self._voice_worker.isRunning():
            return
        self._avatar.set_state("listening")
        self._status_text.setText("LISTENING...")
        self._voice_worker = VoiceWorker()
        self._voice_worker.heard.connect(self._on_voice_heard)
        self._voice_worker.listening.connect(self._on_listening_state)
        self._voice_worker.start()

    @pyqtSlot(str)
    def _on_voice_heard(self, text: str):
        self._text_input.setText(text)
        self._send_text(text)
        self._voice_btn.setChecked(False)

    @pyqtSlot(bool)
    def _on_listening_state(self, active: bool):
        if not active:
            self._voice_btn.setChecked(False)
            if self._avatar._state == "listening":
                self._avatar.set_state("idle")
                self._status_text.setText("SYSTEMS ONLINE")

    # ─── CHAT HELPERS ────────────────────────────────────────
    def _add_user_message(self, text: str):
        bubble = ChatBubble(f"👤  {text}", is_user=True)
        self._chat_layout.addWidget(bubble)
        self._scroll_to_bottom()

    def _add_jarvis_message(self, text: str):
        bubble = ChatBubble(f"🤖  {text}", is_user=False)
        self._chat_layout.addWidget(bubble)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        ))

    def _clear_chat(self):
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._greet()

    def closeEvent(self, event):
        # Clean up workers
        for w in self._brain_workers:
            w.quit()
        event.accept()
