from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .chat_client import ChatClient, read_api_key
from .platform_window import (
    apply_overlay_window_attributes,
    elevate_overlay_window,
    overlay_window_flags,
)
from .resource_manager import resource_path
from .screen_manager import clamp_position, screen_for_point

_TAIL_HEIGHT = 16
_TAIL_HALF_WIDTH = 14
_PADDING = 12
_RADIUS = 18
_AVATAR_SIZE = 36
_BUBBLE_MAX_WIDTH = 190


def _circular_pixmap(source: QPixmap, size: int = _AVATAR_SIZE) -> QPixmap:
    if source.isNull():
        fallback = QPixmap(size, size)
        fallback.fill(QColor("#d8d0c4"))
        source = fallback
    scaled = source.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    # Center-crop to square before masking.
    x = max(0, (scaled.width() - size) // 2)
    y = max(0, (scaled.height() - size) // 2)
    cropped = scaled.copy(x, y, size, size)

    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, cropped)
    painter.end()
    return result


def _load_user_avatar() -> QPixmap:
    candidates = [
        resource_path("assets", "user_avatar.png"),
        resource_path("assets", "app_icon", "app_icon.png"),
    ]
    for path in candidates:
        if Path(path).is_file():
            return _circular_pixmap(QPixmap(str(path)))
    return _circular_pixmap(QPixmap())


def _load_pet_avatar() -> QPixmap:
    candidates = [
        resource_path("assets", "characters", "main_character", "avatar.png"),
        resource_path("assets", "characters", "main_character", "idle", "001.png"),
    ]
    for path in candidates:
        if Path(path).is_file():
            return _circular_pixmap(QPixmap(str(path)))
    return _circular_pixmap(QPixmap())


class ChatBubbleLabel(QLabel):
    """Rounded chat bubble with WeChat-like colors."""

    def __init__(self, text: str, *, mine: bool, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._mine = mine
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        self.setMaximumWidth(_BUBBLE_MAX_WIDTH)
        bg = "#95ec69" if mine else "#ffffff"
        self.setStyleSheet(
            f"""
            QLabel {{
                background: {bg};
                color: #111111;
                border: 1px solid {"#7bcf55" if mine else "#e5e5e5"};
                border-radius: 10px;
                padding: 8px 10px;
                font-size: 13px;
            }}
            """
        )


class MessageRow(QWidget):
    """One WeChat/QQ-style row: pet left, user right."""

    def __init__(
        self,
        text: str,
        *,
        mine: bool,
        avatar: QPixmap,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.bubble = ChatBubbleLabel(text, mine=mine)

        avatar_label = QLabel()
        avatar_label.setFixedSize(_AVATAR_SIZE, _AVATAR_SIZE)
        avatar_label.setPixmap(avatar)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 2, 0, 2)
        row.setSpacing(8)

        if mine:
            row.addStretch(1)
            row.addWidget(self.bubble, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            row.addWidget(avatar_label, 0, Qt.AlignmentFlag.AlignTop)
        else:
            row.addWidget(avatar_label, 0, Qt.AlignmentFlag.AlignTop)
            row.addWidget(self.bubble, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            row.addStretch(1)

    def set_text(self, text: str) -> None:
        self.bubble.setText(text)

    def append_text(self, text: str) -> None:
        self.bubble.setText(self.bubble.text() + text)


class SystemRow(QWidget):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #8a847c; font-size: 11px; padding: 4px 8px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.addWidget(label)


class ChatWindow(QWidget):
    """Frameless floating chat panel with WeChat/QQ-style message rows."""

    visibility_changed = Signal(bool)

    def __init__(self, client: ChatClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.client = client
        self._anchor: QWidget | None = None
        self._streaming = False
        self._assistant_started = False
        self._last_user_text = ""
        self._streaming_row: MessageRow | None = None
        self._user_avatar = _load_user_avatar()
        self._pet_avatar = _load_pet_avatar()

        self.setWindowTitle("桌宠聊天")
        self.setWindowFlags(overlay_window_flags(on_top=True, accept_focus=True))
        apply_overlay_window_attributes(self, on_top=True, accept_focus=True)
        self.setFixedWidth(340)
        self.setMinimumHeight(280)
        self.resize(340, 360)

        self.status_label = QLabel(self._status_text())
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("bubbleStatus")

        self.close_button = QPushButton("×", self)
        self.close_button.setObjectName("bubbleClose")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.hide)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(self.status_label, stretch=1)
        header.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignTop)

        self._list_host = QWidget()
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(2, 2, 2, 2)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch(1)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(self._list_host)
        self.scroll.setObjectName("bubbleScroll")

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("说点什么…")
        self.input.setObjectName("bubbleInput")
        self.send_button = QPushButton("发送", self)
        self.stop_button = QPushButton("停", self)
        self.clear_button = QPushButton("清空", self)
        for button in (self.send_button, self.stop_button, self.clear_button):
            button.setObjectName("bubbleBtn")
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedWidth(36)
        self.clear_button.setFixedWidth(44)
        self.send_button.setFixedWidth(44)

        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        input_row.addWidget(self.input, stretch=1)
        input_row.addWidget(self.send_button)
        input_row.addWidget(self.stop_button)
        input_row.addWidget(self.clear_button)

        body = QVBoxLayout()
        body.setContentsMargins(_PADDING, _PADDING, _PADDING, _PADDING + _TAIL_HEIGHT)
        body.setSpacing(8)
        body.addLayout(header)
        body.addWidget(self.scroll, stretch=1)
        body.addLayout(input_row)
        self.setLayout(body)

        self.setStyleSheet(
            """
            QLabel#bubbleStatus { color: #6b6560; font-size: 11px; }
            QPushButton#bubbleClose {
                background: transparent; border: none; color: #8a847c;
                font-size: 18px; font-weight: bold;
            }
            QPushButton#bubbleClose:hover { color: #2b2b2b; }
            QScrollArea#bubbleScroll { background: transparent; border: none; }
            QScrollArea#bubbleScroll > QWidget > QWidget { background: transparent; }
            QLineEdit#bubbleInput {
                background: #fffdf8; border: 1.5px solid #2b2b2b; border-radius: 10px;
                padding: 6px 10px; color: #1f1f1f; font-size: 13px;
            }
            QPushButton#bubbleBtn {
                background: #fffdf8; border: 1.5px solid #2b2b2b; border-radius: 10px;
                padding: 5px 8px; color: #1f1f1f; font-size: 12px;
            }
            QPushButton#bubbleBtn:hover { background: #f3ebe0; }
            QPushButton#bubbleBtn:disabled { color: #a8a29a; border-color: #c4beb6; }
            """
        )

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
            return "对白"
        return "未配置 API 密钥（设置里填写）"

    def refresh_status(self) -> None:
        self.status_label.setText(self._status_text())

    def focus_input(self) -> None:
        self.input.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def show_near(self, anchor: QWidget) -> None:
        self._anchor = anchor
        self.refresh_status()
        self.reposition()
        self.show()
        elevate_overlay_window(self, activate=True)
        self.focus_input()
        self.visibility_changed.emit(True)

    def reposition(self) -> None:
        if self._anchor is None or not self._anchor.isVisible():
            return
        anchor = self._anchor.frameGeometry()
        desired = QPoint(
            anchor.center().x() - self.width() // 2,
            anchor.top() - self.height() + 10,
        )
        screen = screen_for_point(anchor.center())
        geo = screen.availableGeometry()
        if desired.y() < geo.top():
            desired.setY(anchor.top() + 12)
            desired.setX(anchor.right() + 8)
            if desired.x() + self.width() > geo.right():
                desired.setX(anchor.left() - self.width() - 8)
        self.move(clamp_position(desired, self.size(), geo))

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        body = QRectF(1.5, 1.5, self.width() - 3, self.height() - _TAIL_HEIGHT - 3)
        path = QPainterPath()
        path.addRoundedRect(body, _RADIUS, _RADIUS)
        tip_x = body.center().x()
        tip_y = float(self.height() - 2)
        tail = QPainterPath()
        tail.moveTo(tip_x - _TAIL_HALF_WIDTH, body.bottom() - 1)
        tail.lineTo(tip_x, tip_y)
        tail.lineTo(tip_x + _TAIL_HALF_WIDTH, body.bottom() - 1)
        tail.closeSubpath()
        path = path.united(tail)
        painter.setPen(QPen(QColor("#2b2b2b"), 2.2))
        painter.setBrush(QColor("#efeae3"))
        painter.drawPath(path)

    def _scroll_to_bottom(self) -> None:
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _add_row(self, widget: QWidget) -> None:
        # Insert above the trailing stretch.
        self._list_layout.insertWidget(self._list_layout.count() - 1, widget)
        self._scroll_to_bottom()

    def _append_user(self, text: str) -> None:
        self._add_row(MessageRow(text, mine=True, avatar=self._user_avatar))

    def _append_pet(self, text: str) -> MessageRow:
        row = MessageRow(text, mine=False, avatar=self._pet_avatar)
        self._add_row(row)
        return row

    def _append_system(self, text: str) -> None:
        self._add_row(SystemRow(text))

    def _send(self) -> None:
        if self._streaming:
            return
        text = self.input.text().strip()
        if not text:
            return
        self._last_user_text = text
        self.input.clear()
        self._append_user(text)
        self._begin_streaming()
        self.client.send_message(text)

    def _begin_streaming(self) -> None:
        self._streaming = True
        self._assistant_started = False
        self._streaming_row = None
        self.send_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.input.setEnabled(False)

    def _end_streaming(self) -> None:
        self._streaming = False
        self._assistant_started = False
        self._streaming_row = None
        self.send_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.input.setEnabled(True)
        self.focus_input()

    def _append_delta(self, delta: str) -> None:
        if not self._assistant_started:
            self._assistant_started = True
            self._streaming_row = self._append_pet(delta)
            return
        if self._streaming_row is not None:
            self._streaming_row.append_text(delta)
            self._scroll_to_bottom()

    def _on_finished(self, _content: str) -> None:
        self._end_streaming()

    def _on_error(self, message: str) -> None:
        self._append_system(message)
        if self._last_user_text:
            self.input.setText(self._last_user_text)
            self._last_user_text = ""
        self._end_streaming()

    def _on_cancelled(self) -> None:
        self._append_system("已停止生成。")
        if self._last_user_text:
            self.input.setText(self._last_user_text)
            self._last_user_text = ""
        self._end_streaming()

    def _clear_conversation(self) -> None:
        if self._streaming:
            return
        self.client.reset_conversation()
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._last_user_text = ""
        self.focus_input()

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._streaming:
            self.client.cancel()
        event.accept()
        self.visibility_changed.emit(False)
