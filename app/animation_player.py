from pathlib import Path
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap, QTransform

from .character_manager import CharacterManager


def natural_frame_sort_key(path: Path | str):
    path = Path(path)
    return (int(path.stem) if path.stem.isdigit() else 10**9, path.name.lower())


def sorted_frame_paths(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.png"), key=natural_frame_sort_key)


class AnimationPlayer(QObject):
    frame_changed = Signal(QPixmap)
    finished = Signal(str)

    def __init__(self, characters: CharacterManager, parent=None):
        super().__init__(parent)
        self.characters = characters
        self.timer = QTimer(self, timeout=self._advance)
        self.cache: dict[Path, QPixmap] = {}
        self.frames: list[QPixmap] = []
        self.name = "idle"
        self.index = 0
        self.loop = True
        self.mirrored = False
        self.speed = 1.0

    def preload(self) -> None:
        for name in self.characters.metadata.get("animations", {}):
            for path in sorted_frame_paths(self.characters.animation(name).folder):
                self._pixmap(path)

    def _pixmap(self, path: Path) -> QPixmap:
        if path not in self.cache:
            image = QImage(str(path))
            self.cache[path] = QPixmap.fromImage(image)
        return self.cache[path]

    def play(self, name: str, mirrored: bool = False) -> None:
        spec = self.characters.animation(name)
        paths = sorted_frame_paths(spec.folder)
        if not paths and name != "idle":
            spec = self.characters.animation("idle")
            paths = sorted_frame_paths(spec.folder)
        self.frames = [self._pixmap(path) for path in paths]
        self.name, self.loop, self.mirrored, self.index = spec.name, spec.loop, mirrored, 0
        if not self.frames:
            self.timer.stop()
            return
        self._emit()
        self.timer.start(max(16, round(1000 / max(1, spec.fps * self.speed))))

    def _emit(self) -> None:
        frame = self.frames[self.index]
        if self.mirrored:
            frame = frame.transformed(QTransform().scale(-1, 1))
        self.frame_changed.emit(frame)

    def _advance(self) -> None:
        if not self.frames:
            return
        self.index += 1
        if self.index >= len(self.frames):
            if not self.loop:
                self.timer.stop()
                self.finished.emit(self.name)
                return
            self.index = 0
        self._emit()
