from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QLabel



# =====================================
# Worker (runs brain in background)
# =====================================
class BrainWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        from brain.brain import process_text
        reply = process_text(self.text)
        self.finished.emit(reply)

# =====================================
# voices recognition worker
# =====================================
class VoiceWorker(QObject):
    finished = pyqtSignal(str)

    def run(self):
        from body.listen import listen
        text = listen()
        self.finished.emit(text or "")

# =====================================
# Speak Worker         
# =====================================
class SpeakWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        from body.speak import speak
        speak(self.text)
        self.finished.emit()
        print("[UI] SpeakWorker running")




# =====================================
# Main Window
# =====================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")
        self.setGeometry(300, 150, 900, 600)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Chat display
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.append("Jarvis: Online.")
        layout.addWidget(self.chat_area)

        
        # Input row
        input_layout = QHBoxLayout()

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type a command...")
        self.input_box.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)

        self.mic_btn = QPushButton("🎙️")
        self.mic_btn.clicked.connect(self.start_listening)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(send_btn)
        input_layout.addWidget(self.mic_btn)

        layout.addLayout(input_layout)
        self.setLayout(layout)

        # Status indicator
        self.status_label = QLabel("● Idle")
        self.status_label.setStyleSheet("color: #00ff88; font-weight: bold;")
        layout.addWidget(self.status_label)

    # =====================================
    # Send message (NON-BLOCKING)
    # =====================================
    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return

        # Show user message
        self.chat_area.append(f"You: {text}")
        self.input_box.clear()
        self.input_box.setEnabled(False)

        # Thinking indicator
        self.set_status("thinking")

        self.chat_area.append("Jarvis: Thinking...")

        # Thread setup
        self.thread = QThread()
        self.worker = BrainWorker(text)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_response)          # type: ignore
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    # =====================================
    # Handle response from brain
    # =====================================
    def on_response(self, reply: str):
        # Remove "Thinking..." line
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()

        # Show response in UI
        self.chat_area.append(f"Jarvis: {reply}")

        # Auto-scroll
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

        # Speak reply (threaded)
        self.start_speaking(reply)

        self.input_box.setEnabled(True)

    def start_listening(self):
        self.input_box.setEnabled(False)
        self.set_status("listening")

        self.chat_area.append("Jarvis: Listening...")

        self.voice_thread = QThread()
        self.voice_worker = VoiceWorker()
        self.voice_worker.moveToThread(self.voice_thread)

        self.voice_thread.started.connect(self.voice_worker.run)
        self.voice_worker.finished.connect(self.on_voice_input)     # type: ignore
        self.voice_worker.finished.connect(self.voice_thread.quit)
        self.voice_worker.finished.connect(self.voice_worker.deleteLater)
        self.voice_thread.finished.connect(self.voice_thread.deleteLater)

        self.voice_thread.start()


    def on_voice_input(self, text: str):
        # Remove "Listening..." line
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()

        self.input_box.setEnabled(True)

        if not text:
            self.chat_area.append("Jarvis: I didn’t catch that.")
            return

        # Show recognized speech
        self.chat_area.append(f"You: {text}")

        # Process like typed input
        self.send_voice_text(text)

    def send_voice_text(self, text: str):
        self.input_box.setEnabled(False)
        self.set_status("thinking")

        self.chat_area.append("Jarvis: Thinking...")

        self.thread = QThread()
        self.worker = BrainWorker(text)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_response)              # type: ignore
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def start_speaking(self, text: str):
        self.mic_btn.setEnabled(False)
        self.set_status("speaking")


        self.speak_thread = QThread()
        self.speak_worker = SpeakWorker(text)

        # IMPORTANT: keep references
        self.speak_worker.moveToThread(self.speak_thread)

        self.speak_thread.started.connect(self.speak_worker.run)
        self.speak_worker.finished.connect(self.on_speaking_done)
        self.speak_worker.finished.connect(self.speak_thread.quit)
        self.speak_worker.finished.connect(self.speak_worker.deleteLater)
        self.speak_thread.finished.connect(self.speak_thread.deleteLater)

        self.speak_thread.start()

    def on_speaking_done(self):
        self.mic_btn.setEnabled(True)
        self.set_status("idle")



    def set_status(self, state: str):
        colors = {
            "idle": "#00ff88",
            "listening": "#00bfff",
            "thinking": "#ffd700",
            "speaking": "#ff0800",
        }

        labels = {
            "idle": "● Idle",
            "listening": "● Listening",
            "thinking": "● Thinking",
            "speaking": "● Speaking",
        }

        color = colors.get(state, "#ffffff")
        label = labels.get(state, "● Unknown")

        self.status_label.setText(label)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
