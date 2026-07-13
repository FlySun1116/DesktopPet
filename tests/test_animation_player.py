from pathlib import Path

import pytest


animation_module = pytest.importorskip("app.animation_player")


def _sort_key():
    return getattr(animation_module, "natural_frame_sort_key", getattr(animation_module, "frame_sort_key", None))


def test_numeric_frame_sorting():
    key = _sort_key()
    assert key is not None, "animation_player 应公开自然帧排序键"
    names = [Path("10.png"), Path("002.png"), Path("1.png")]
    assert [p.name for p in sorted(names, key=key)] == ["1.png", "002.png", "10.png"]


def test_non_png_files_do_not_enter_frame_sequence(tmp_path):
    for name in ("001.png", "002.PNG", "notes.txt", ".DS_Store"):
        (tmp_path / name).write_bytes(b"x")
    loader = getattr(animation_module, "discover_frames", None)
    if loader is None:
        pytest.skip("由播放器实例负责加载时在集成测试覆盖")
    assert [p.name for p in loader(tmp_path)] == ["001.png", "002.PNG"]

