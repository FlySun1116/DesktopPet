"""Import QA-approved hatch-pet frames into the desktop-pet character pack.

Only the explicit mapping below is promoted. Other actions remain unmistakable
placeholders until a later reviewed import.
"""
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
HATCH_FRAMES = ROOT / "artwork" / "hatch_run" / "frames"
CHARACTER = ROOT / "assets" / "characters" / "main_character"
MAPPING = {
    "idle": "idle",
    "running-right": "walk",
    "waving": "wave",
    "jumping": "happy",
}
STATUS = {
    "idle": "generated_reviewed",
    "walk": "generated_reviewed",
    "wave": "generated_reviewed",
    "happy": "generated_reviewed",
    "sit": "placeholder",
    "sleep": "placeholder",
    "surprised": "placeholder",
    "dragged": "placeholder",
    "fall": "placeholder",
}
CANVAS = (768, 768)
BOTTOM_MARGIN = 20
MAX_SPRITE = (680, 680)


def natural_key(path: Path):
    return (int(path.stem) if path.stem.isdigit() else 10**9, path.name.lower())


def place_on_canvas(source: Path) -> Image.Image:
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"Blank frame: {source}")
    sprite = image.crop(bbox)
    scale = min(MAX_SPRITE[0] / sprite.width, MAX_SPRITE[1] / sprite.height)
    size = (max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale)))
    sprite = sprite.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    x = (CANVAS[0] - sprite.width) // 2
    y = CANVAS[1] - BOTTOM_MARGIN - sprite.height
    canvas.alpha_composite(sprite, (x, y))
    return canvas


def main() -> int:
    for source_name, target_name in MAPPING.items():
        source_dir = HATCH_FRAMES / source_name
        frames = sorted(source_dir.glob("*.png"), key=natural_key)
        if not frames:
            raise FileNotFoundError(f"No approved hatch frames: {source_dir}")
        target_dir = CHARACTER / target_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for old in target_dir.glob("*.png"):
            old.unlink()
        for index, frame in enumerate(frames, 1):
            place_on_canvas(frame).save(target_dir / f"{index:03}.png", optimize=True)
        print(f"Imported {source_name} -> {target_name}: {len(frames)} frames")

    config_path = CHARACTER / "character.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["placeholder"] = True
    config["asset_status"] = STATUS
    for name, status in STATUS.items():
        if name in config.get("animations", {}):
            config["animations"][name]["placeholder"] = status == "placeholder"
            config["animations"][name]["asset_status"] = status
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
