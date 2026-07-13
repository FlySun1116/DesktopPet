import random
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QCursor, QPixmap
from PySide6.QtWidgets import QLabel, QMenu, QWidget, QMessageBox

from .animation_player import AnimationPlayer
from .constants import PetState
from .screen_manager import clamp_position, screen_for_point


class PetWindow(QWidget):
    def __init__(self, config, character, parent=None):
        super().__init__(None)
        self.application = parent
        self.config, self.character = config, character
        self.state_machine = None
        self.dragging = False
        self._press_global = QPoint(); self._window_at_press = QPoint(); self._did_drag = False
        self.label = QLabel(self); self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.player = AnimationPlayer(character, self)
        self.player.frame_changed.connect(self._show_frame)
        self.player.finished.connect(lambda _name: self.set_state(PetState.IDLE))
        self.walk_timer = QTimer(self, timeout=self._walk_step)
        self.click_timer = QTimer(self, singleShot=True, interval=220, timeout=lambda: self.set_state(PetState.SURPRISED))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint); self.setWindowFlag(Qt.Tool)
        self.apply_settings(first=True)

    def bind_state_machine(self, machine):
        self.state_machine = machine
        machine.changed.connect(self._state_changed)

    def apply_settings(self, first=False):
        self.player.speed = float(self.config.get("animation_speed", 1.0))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(self.config.get("always_on_top", True)))
        if not first: self.show()
        self.player.play(self.player.name, self.player.mirrored)

    def set_state(self, state):
        if self.state_machine: self.state_machine.transition(state, force=True)

    def _state_changed(self, _old, state):
        name, mirror = self.state_machine.animation_for(state)
        self.player.play(name, mirror)
        if state in (PetState.WALK_LEFT, PetState.WALK_RIGHT): self.walk_timer.start(30)
        else: self.walk_timer.stop()

    def _show_frame(self, pixmap: QPixmap):
        scale = float(self.config.get("character_scale", self.character.default_scale))
        target = pixmap.scaled(max(1, int(pixmap.width()*scale)), max(1, int(pixmap.height()*scale)), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        foot = self.geometry().bottomLeft()
        self.label.setPixmap(target); self.label.resize(target.size()); self.resize(target.size())
        if self.isVisible(): self.move(self.clamped(QPoint(self.x(), foot.y()-self.height()+1)))

    def clamped(self, point):
        screen = screen_for_point(point + QPoint(self.width()//2, self.height()//2))
        return clamp_position(point, self.size(), screen.availableGeometry())

    def reset_position(self):
        geo = screen_for_point(QCursor.pos()).availableGeometry()
        self.move(geo.right()-self.width()+1, geo.bottom()-self.height()+1)

    def _walk_step(self):
        direction = -1 if self.state_machine.state == PetState.WALK_LEFT else 1
        step = max(1, round(float(self.config.get("move_speed", 100))*0.03))*direction
        intended = QPoint(self.x()+step, self.y()); actual = self.clamped(intended)
        self.move(actual)
        if actual.x() != intended.x(): self.set_state(PetState.WALK_RIGHT if direction < 0 else PetState.WALK_LEFT)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_global = event.globalPosition().toPoint(); self._window_at_press = self.pos(); self._did_drag = False

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_global
            if delta.manhattanLength() > 5:
                self.dragging = self._did_drag = True; self.set_state(PetState.DRAGGED); self.move(self.clamped(self._window_at_press + delta))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dragging:
                self.dragging = False; self.set_state(PetState.FALL); self.config.set("last_position", [self.x(), self.y()]); self.config.save()
            elif not self._did_drag: self.click_timer.start()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton: self.click_timer.stop(); self.set_state(PetState.HAPPY)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        actions = [("挥手", PetState.WAVE), ("坐下", PetState.SIT), ("睡觉", PetState.SLEEP), ("随机动作", random.choice([PetState.WAVE, PetState.HAPPY, PetState.SURPRISED]))]
        for text, state in actions: menu.addAction(text, lambda checked=False, s=state: self.set_state(s))
        menu.addSeparator(); menu.addAction("暂停自动行为", self.application.behavior.pause); menu.addAction("恢复自动行为", self.application.behavior.resume)
        menu.addAction("重置位置", self.reset_position); menu.addAction("设置", self.application.show_settings)
        menu.addAction("关于", lambda: QMessageBox.about(self, "关于", "真人动漫形象桌宠 1.0")); menu.addAction("退出", self.application.quit)
        menu.exec(event.globalPos())

    def closeEvent(self, event):
        event.ignore(); self.hide()
