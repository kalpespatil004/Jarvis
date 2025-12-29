from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from brain.brain import process_text



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

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)
        self.setLayout(layout)

    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return

        # Show user message
        self.chat_area.append(f"You: {text}")
        self.input_box.clear()

        # Get Jarvis response
        response = process_text(text)

        if response:
            self.chat_area.append(f"Jarvis: {response}")
