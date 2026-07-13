from enum import Enum

APP_NAME = "AnimePersonDesktopPet"
ORG_NAME = "DesktopPet"
CHARACTER_ID = "main_character"


class PetState(str, Enum):
    IDLE = "idle"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    SIT = "sit"
    SLEEP = "sleep"
    WAVE = "wave"
    HAPPY = "happy"
    SURPRISED = "surprised"
    DRAGGED = "dragged"
    FALL = "fall"
