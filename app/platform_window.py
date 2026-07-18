"""Platform helpers: keep overlay windows visually on top without stealing focus."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def apply_overlay_window_attributes(widget: QWidget, *, on_top: bool = True, accept_focus: bool = False) -> None:
    """Visual overlay chrome: on-top stacking, but do not grab app focus by default.

    accept_focus=False  → pet: mouse works, keyboard focus stays with other apps
    accept_focus=True   → chat bubble: can take focus when the user opens it
    """
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    # Showing / raising must not yank focus away from Cursor, browsers, etc.
    widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, not accept_focus)
    if sys.platform == "darwin":
        # Keep Qt.Tool panels visible while this process is inactive.
        widget.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, on_top)


def overlay_window_flags(*, on_top: bool = True, accept_focus: bool = False) -> Qt.WindowType:
    flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
    if on_top:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    if not accept_focus:
        flags |= Qt.WindowType.WindowDoesNotAcceptFocus
    return flags


def elevate_overlay_window(widget: QWidget, *, activate: bool = False) -> None:
    """Re-assert z-order without activating, unless activate=True (chat open)."""
    if not widget.isVisible():
        return
    try:
        widget.winId()
        if sys.platform == "win32":
            _elevate_windows(widget, activate=activate)
        if activate:
            widget.raise_()
            widget.activateWindow()
        # When not activating: rely on WindowStaysOnTopHint / Tool level.
        # Calling raise_() here can steal focus on macOS.
    except Exception:
        logger.exception("elevate_overlay_window failed")


def _elevate_windows(widget: QWidget, *, activate: bool) -> None:
    try:
        import ctypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        hwnd = int(widget.winId())
        HWND_TOPMOST = -1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        SWP_SHOWWINDOW = 0x0040
        flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
        if not activate:
            flags |= SWP_NOACTIVATE
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
    except Exception:
        logger.debug("Win32 elevate failed", exc_info=True)
