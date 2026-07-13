import json

import pytest


config_module = pytest.importorskip("app.config_manager")
ConfigManager = config_module.ConfigManager


def _manager(tmp_path, defaults, user=None):
    default_path = tmp_path / "default.json"
    user_path = tmp_path / "user.json"
    default_path.write_text(json.dumps(defaults), encoding="utf-8")
    if user is not None:
        user_path.write_text(json.dumps(user), encoding="utf-8")
    try:
        return ConfigManager(default_path=default_path, user_path=user_path), user_path
    except TypeError:
        return ConfigManager(str(default_path), str(user_path)), user_path


def _get(manager, key):
    getter = getattr(manager, "get", None)
    return getter(key) if getter else manager.config[key]


def test_defaults_and_recursive_user_merge(tmp_path):
    manager, user_path = _manager(
        tmp_path,
        {"scale": 0.36, "behavior": {"walk": 0.2, "wave": 0.1}},
        {"behavior": {"walk": 0.8}},
    )
    assert _get(manager, "scale") == 0.36
    behavior = _get(manager, "behavior")
    assert behavior == {"walk": 0.8, "wave": 0.1}


def test_corrupt_user_config_falls_back_to_defaults(tmp_path):
    manager, user_path = _manager(tmp_path, {"scale": 0.36})
    user_path.write_text("{broken", encoding="utf-8")
    manager, _ = _manager(tmp_path, {"scale": 0.36})
    assert _get(manager, "scale") == 0.36


def test_save_does_not_modify_packaged_defaults(tmp_path):
    manager, user_path = _manager(tmp_path, {"scale": 0.36})
    before = (tmp_path / "default.json").read_bytes()
    if hasattr(manager, "set"):
        manager.set("scale", 0.5)
    else:
        manager.config["scale"] = 0.5
    manager.save()
    assert user_path.exists()
    assert (tmp_path / "default.json").read_bytes() == before
