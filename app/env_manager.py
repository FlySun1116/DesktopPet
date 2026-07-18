from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import dotenv_values, load_dotenv, set_key

from .resource_manager import user_data_dir

API_KEY_ENV = "DESKTOP_PET_API_KEY"
BASE_URL_ENV = "DESKTOP_PET_BASE_URL"


def env_path() -> Path:
    if getattr(sys, "frozen", False):
        return user_data_dir() / ".env"
    return Path(__file__).resolve().parents[1] / ".env"


def load_project_env(path: Path | None = None) -> None:
    load_dotenv(path or env_path(), override=True)


def read_env_value(name: str, path: Path | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None:
        stored = dotenv_values(path or env_path()).get(name)
        value = stored if isinstance(stored, str) else None
    value = value.strip() if value else ""
    return value or None


def save_env_value(name: str, value: str, path: Path | None = None) -> None:
    target = path or env_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch(exist_ok=True)
    clean_value = value.strip()
    set_key(str(target), name, clean_value, quote_mode="always")
    if clean_value:
        os.environ[name] = clean_value
    else:
        os.environ.pop(name, None)
