import random
from PySide6.QtCore import QObject, QTimer
from .constants import PetState


class BehaviorController(QObject):
    def __init__(self, window, config, parent=None):
        super().__init__(parent)
        self.window, self.config = window, config
        self.timer = QTimer(self, timeout=self.choose)
        self.resume()

    def resume(self):
        self.timer.start(int(self.config.get("behavior.interval_ms", 7000)))

    def pause(self):
        self.timer.stop()
        self.window.set_state(PetState.IDLE)

    def choose(self):
        if not self.config.get("auto_move", True) or self.window.dragging:
            return
        weights = self.config.get("behavior.probabilities", {})
        names = ["idle", "walk", "sit", "sleep", "wave"]
        state = random.choices(names, weights=[float(weights.get(n, 1)) for n in names], k=1)[0]
        if state == "walk":
            state = random.choice([PetState.WALK_LEFT, PetState.WALK_RIGHT])
        else:
            state = PetState(state)
        self.window.set_state(state)
