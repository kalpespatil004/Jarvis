from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from brain.brain import process_text


class BrainWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        response = process_text(self.text)
        self.finished.emit(response or "")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")
        self.setGeometry(250, 120, 1000, 640)

        self.avatar_state = "idle"
        self.speaking_tick = False
        self._thread: QThread | None = None
        self._worker: BrainWorker | None = None

        self.avatar_map = {
            "idle": "(＾▽＾)",
            "thinking": "(・_・?)",
            "speaking": "(＾◡＾)",
            "speaking_alt": "(＾o＾)",
            "listening": "( •̀ ω •́ )✧",
        }

        self.speaking_timer = QTimer(self)
        self.speaking_timer.setInterval(120)
        self.speaking_timer.timeout.connect(self._animate_speaking)

        self.init_ui()
        self.set_avatar_state("idle")

    def init_ui(self):
        root_layout = QHBoxLayout()

        # Avatar panel
        avatar_panel = QFrame()
        avatar_panel.setObjectName("avatarPanel")
        avatar_layout = QVBoxLayout(avatar_panel)

        title = QLabel("Jarvis Avatar")
        title.setObjectName("avatarTitle")
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("avatarFace")
        self.state_label = QLabel()
        self.state_label.setObjectName("avatarState")

        avatar_layout.addWidget(title)
        avatar_layout.addWidget(self.avatar_label, 1)
        avatar_layout.addWidget(self.state_label)

        # Chat panel
        chat_panel = QFrame()
        chat_layout = QVBoxLayout(chat_panel)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.append("Jarvis: Online. UI avatar module initialized.")

        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type a command...")
        self.input_box.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)

        chat_layout.addWidget(self.chat_area)
        chat_layout.addLayout(input_layout)

        root_layout.addWidget(avatar_panel, 2)
        root_layout.addWidget(chat_panel, 5)
        self.setLayout(root_layout)

        self.setStyleSheet(
            """
            QWidget {
                background: #0f1419;
                color: #e6edf3;
                font-size: 14px;
            }
            #avatarPanel {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 10px;
            }
            #avatarTitle {
                font-size: 16px;
                font-weight: 600;
                color: #7ee787;
            }
            #avatarFace {
                font-size: 54px;
                border: 1px solid #30363d;
                border-radius: 8px;
                background: #0d1117;
                qproperty-alignment: AlignCenter;
                min-height: 240px;
            }
            #avatarState {
                color: #79c0ff;
                font-size: 13px;
            }
            QTextEdit, QLineEdit {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton {
                background: #238636;
                color: white;
                border-radius: 8px;
                padding: 8px 14px;
            }
            QPushButton:disabled {
                background: #2d333b;
                color: #8b949e;
            }
            """
        )

    def set_avatar_state(self, state: str):
        self.avatar_state = state

        if state == "speaking":
            self.speaking_tick = False
            self.speaking_timer.start()
            self.avatar_label.setText(self.avatar_map["speaking"])
        else:
            self.speaking_timer.stop()
            self.avatar_label.setText(self.avatar_map.get(state, self.avatar_map["idle"]))

        self.state_label.setText(f"State: {state}")

    def _animate_speaking(self):
        self.speaking_tick = not self.speaking_tick
        key = "speaking_alt" if self.speaking_tick else "speaking"
        self.avatar_label.setText(self.avatar_map[key])

    def send_message(self):
        text = self.input_box.text().strip()
        if not text or self._thread is not None:
            return

        self.chat_area.append(f"You: {text}")
        self.input_box.clear()

        self.set_avatar_state("thinking")
        self.send_btn.setDisabled(True)
        self.input_box.setDisabled(True)

        self._thread = QThread(self)
        self._worker = BrainWorker(text)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._handle_response)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_complete)

        self._thread.start()

    def _handle_response(self, response: str):
        if response:
            self.chat_area.append(f"Jarvis: {response}")
            self.set_avatar_state("speaking")
            QTimer.singleShot(1200, lambda: self.set_avatar_state("idle"))
        else:
            self.set_avatar_state("idle")

    def _on_thread_complete(self):
        self._thread = None
        self._worker = None
        self.send_btn.setDisabled(False)
        self.input_box.setDisabled(False)
        self.input_box.setFocus()
