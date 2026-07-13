import json

import pytest


character_module = pytest.importorskip("app.character_manager")
CharacterManager = character_module.CharacterManager


def test_character_config_is_dynamic_and_resolves_animation_folder(tmp_path, monkeypatch):
    root = tmp_path / "hero"
    (root / "idle").mkdir(parents=True)
    (root / "idle" / "001.png").write_bytes(b"placeholder")
    data = {
        "id": "hero", "canvas_size": [768, 768], "anchor": "bottom_center",
        "animations": {"idle": {"folder": "idle", "fps": 7, "loop": True}},
    }
    path = root / "character.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(character_module, "resource_path", lambda *parts: root)
    manager = CharacterManager("hero")
    animation = manager.animation("idle")
    folder = animation.get("path", animation.get("folder")) if isinstance(animation, dict) else animation.folder
    assert str(folder).replace("\\", "/").endswith("idle")


def test_missing_action_falls_back_to_idle(tmp_path, monkeypatch):
    root = tmp_path / "hero"
    root.mkdir()
    path = root / "character.json"
    path.write_text(json.dumps({"id": "hero", "animations": {"idle": {"folder": "idle", "fps": 7, "loop": True}}}), encoding="utf-8")
    monkeypatch.setattr(character_module, "resource_path", lambda *parts: root)
    manager = CharacterManager("hero")
    assert manager.animation("does-not-exist").name == "idle"


def test_invalid_character_json_uses_safe_animation_defaults(tmp_path, monkeypatch):
    path = tmp_path / "character.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(character_module, "resource_path", lambda *parts: tmp_path)
    spec = CharacterManager("hero").animation("idle")
    assert spec.name == "idle" and spec.fps == 7 and spec.loop is True
