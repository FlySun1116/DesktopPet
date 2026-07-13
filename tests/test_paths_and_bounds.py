from pathlib import Path

import pytest


def test_clamp_keeps_pet_inside_available_geometry():
    module = pytest.importorskip("app.screen_manager")
    qtcore = pytest.importorskip("PySide6.QtCore")
    clamp = getattr(module, "clamp_to_available_geometry", None)
    assert clamp is not None
    size = qtcore.QSize(200, 300)
    geometry = qtcore.QRect(0, 0, 1920, 1040)
    first = clamp(qtcore.QPoint(-20, 900), size, geometry)
    second = clamp(qtcore.QPoint(1900, -5), size, geometry)
    assert (first.x(), first.y()) == (0, 740)
    assert (second.x(), second.y()) == (1720, 0)


def test_resource_path_works_in_source_tree():
    module = pytest.importorskip("app.resource_manager")
    result = Path(module.resource_path("config/default_config.json"))
    assert result.name == "default_config.json"
    assert result.is_absolute()


def test_user_data_dir_is_not_inside_installation(monkeypatch, tmp_path):
    module = pytest.importorskip("app.resource_manager")
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    result = Path(module.user_data_dir())
    assert str(result).startswith(str(tmp_path / "Roaming"))
    assert "AnimePersonDesktopPet" in str(result)
