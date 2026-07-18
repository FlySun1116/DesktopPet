from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .chat_client import ChatClient, read_api_key


class ChatWindow(QWidget):
    def __init__(self, client: ChatClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.client = client
        self._streaming = False
        self._assistant_started = False
        self._last_user_text = ""

        self.setWindowTitle("桌宠聊天")
        self.setWindowFlag(Qt.WindowType.Window)
        self.resize(420, 520)

        self.status_label = QLabel(self._status_text())
        self.history = QTextEdit(self)
        self.history.setReadOnly(True)
        self.history.setPlaceholderText("和桌宠聊聊吧。")

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("输入消息，按 Enter 发送")
        self.send_button = QPushButton("发送", self)
        self.stop_button = QPushButton("停止", self)
        self.clear_button = QPushButton("清空", self)
        self.stop_button.setEnabled(False)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input, stretch=1)
        input_row.addWidget(self.send_button)
        input_row.addWidget(self.stop_button)
        input_row.addWidget(self.clear_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.history, stretch=1)
        layout.addLayout(input_row)

        self.send_button.clicked.connect(self._send)
        self.stop_button.clicked.connect(self.client.cancel)
        self.clear_button.clicked.connect(self._clear_conversation)
        self.input.returnPressed.connect(self._send)

        self.client.delta_received.connect(self._append_delta)
        self.client.finished.connect(self._on_finished)
        self.client.error.connect(self._on_error)
        self.client.cancelled.connect(self._on_cancelled)

    def _status_text(self) -> str:
        if read_api_key():
            return "API 密钥：已通过 .env 配置"
        return "API 密钥：未配置。请在设置中填写，或编辑项目根目录 .env。"

    def refresh_status(self) -> None:
        self.status_label.setText(self._status_text())

    def focus_input(self) -> None:
        self.input.setFocus()

    def _append_line(self, speaker: str, text: str) -> None:
        self.history.moveCursor(QTextCursor.MoveOperation.End)
        self.history.insertPlainText(f"{speaker}：{text}\n")
        self.history.moveCursor(QTextCursor.MoveOperation.End)

    def _send(self) -> None:
        if self._streaming:
            return
        text = self.input.text().strip()
        if not text:
            return
        self._last_user_text = text
        self.input.clear()
        self._append_line("你", text)
        self._begin_streaming()
        self.client.send_message(text)

    def _begin_streaming(self) -> None:
        self._streaming = True
        self._assistant_started = False
        self.send_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.input.setEnabled(False)

    def _end_streaming(self) -> None:
        self._streaming = False
        self._assistant_started = False
        self.send_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.input.setEnabled(True)
        self.focus_input()

    def _append_delta(self, delta: str) -> None:
        if not self._assistant_started:
            self._assistant_started = True
            self.history.moveCursor(QTextCursor.MoveOperation.End)
            self.history.insertPlainText("桌宠：")
        self.history.moveCursor(QTextCursor.MoveOperation.End)
        self.history.insertPlainText(delta)
        self.history.moveCursor(QTextCursor.MoveOperation.End)

    def _on_finished(self, _content: str) -> None:
        if self._assistant_started:
            self.history.moveCursor(QTextCursor.MoveOperation.End)
            self.history.insertPlainText("\n")
        self._end_streaming()

    def _on_error(self, message: str) -> None:
        if self._assistant_started:
            self.history.moveCursor(QTextCursor.MoveOperation.End)
            self.history.insertPlainText("\n")
        self._append_line("系统", message)
        if self._last_user_text:
            self.input.setText(self._last_user_text)
            self._last_user_text = ""
        self._end_streaming()

    def _on_cancelled(self) -> None:
        if self._assistant_started:
            self.history.moveCursor(QTextCursor.MoveOperation.End)
            self.history.insertPlainText("\n")
        self._append_line("系统", "已停止生成。")
        if self._last_user_text:
            self.input.setText(self._last_user_text)
            self._last_user_text = ""
        self._end_streaming()

    def _clear_conversation(self) -> None:
        if self._streaming:
            return
        self.client.reset_conversation()
        self.history.clear()
        self._last_user_text = ""
        self.focus_input()

    def closeEvent(self, event) -> None:
        if self._streaming:
            self.client.cancel()
        event.accept()
