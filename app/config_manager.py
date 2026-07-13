import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .resource_manager import resource_path, user_data_dir


def deep_merge(base: dict, override: dict) -> dict:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class ConfigManager:
    def __init__(self, default_path: Path | None = None, user_path: Path | None = None):
        self.default_path = default_path or resource_path("config", "default_config.json")
        self.user_path = user_path or user_data_dir() / "user_config.json"
        self.defaults = self._read(self.default_path, required=True)
        self.data = deep_merge(self.defaults, self._read(self.user_path))

    @staticmethod
    def _read(path: Path, required: bool = False) -> dict:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            if required:
                raise RuntimeError(f"Cannot read required configuration: {path}")
            return {}

    def get(self, key: str, default: Any = None) -> Any:
        value: Any = self.data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def set(self, key: str, value: Any) -> None:
        target = self.data
        parts = key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    def save(self) -> None:
        self.user_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.user_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.user_path)

    def reset(self) -> None:
        self.data = deepcopy(self.defaults)
        self.save()
