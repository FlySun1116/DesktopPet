import pytest


state_module = pytest.importorskip("app.state_machine")
PetState = state_module.PetState
PetStateMachine = state_module.PetStateMachine


def _state(machine):
    value = getattr(machine, "state", getattr(machine, "current_state", None))
    return value() if callable(value) else value


def _transition(machine, state):
    method = getattr(machine, "transition", None)
    assert method is not None
    return method(state)


def test_starts_idle():
    assert _state(PetStateMachine()) == PetState.IDLE


def test_drag_has_priority_and_release_recovers():
    machine = PetStateMachine()
    _transition(machine, PetState.SLEEP)
    _transition(machine, PetState.DRAGGED)
    assert _state(machine) == PetState.DRAGGED
    _transition(machine, PetState.IDLE)
    assert _state(machine) == PetState.IDLE


def test_walk_states_map_to_walk_animation_and_mirror():
    machine = PetStateMachine()
    assert machine.animation_for(PetState.WALK_LEFT) == ("walk", True)
    assert machine.animation_for(PetState.WALK_RIGHT) == ("walk", False)
