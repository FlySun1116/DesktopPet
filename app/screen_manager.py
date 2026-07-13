from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QGuiApplication


def clamp_position(position: QPoint, size, geometry: QRect) -> QPoint:
    return QPoint(max(geometry.left(), min(position.x(), geometry.right() - size.width() + 1)),
                  max(geometry.top(), min(position.y(), geometry.bottom() - size.height() + 1)))


def clamp_to_available_geometry(position: QPoint, size, geometry: QRect) -> QPoint:
    return clamp_position(position, size, geometry)


def screen_for_point(point: QPoint):
    return QGuiApplication.screenAt(point) or QGuiApplication.primaryScreen()
