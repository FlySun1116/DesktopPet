from pathlib import Path
import sys
import os


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def user_data_dir() -> Path:
    from .constants import APP_NAME
    return Path(os.environ.get("APPDATA") or Path.home() / ".config") / APP_NAME
