from PySide6.QtCore import QObject, Signal
from .constants import PetState


class PetStateMachine(QObject):
    changed = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = PetState.IDLE

    def transition(self, state: PetState, force: bool = False) -> bool:
        if state == self.state and not force:
            return False
        previous, self.state = self.state, state
        self.changed.emit(previous, state)
        return True

    @staticmethod
    def animation_for(state: PetState) -> tuple[str, bool]:
        if state in (PetState.WALK_LEFT, PetState.WALK_RIGHT):
            # The authored walk frames face screen-right; mirror only for leftward travel.
            return "walk", state == PetState.WALK_LEFT
        return state.value, False
