import json
from dataclasses import dataclass
from pathlib import Path

from .constants import CHARACTER_ID
from .resource_manager import resource_path


@dataclass(frozen=True)
class AnimationSpec:
    name: str
    folder: Path
    fps: float
    loop: bool


class CharacterManager:
    def __init__(self, character_id: str = CHARACTER_ID):
        self.root = resource_path("assets", "characters", character_id)
        self.metadata = json.loads((self.root / "character.json").read_text(encoding="utf-8"))

    @property
    def default_scale(self) -> float:
        return float(self.metadata.get("default_scale", 0.36))

    def animation(self, name: str) -> AnimationSpec:
        animations = self.metadata.get("animations", {})
        actual = name if name in animations else "idle"
        value = animations.get(actual, {})
        return AnimationSpec(actual, self.root / value.get("folder", actual), float(value.get("fps", 7)), bool(value.get("loop", True)))
