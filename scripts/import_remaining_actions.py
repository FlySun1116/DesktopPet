"""Import reviewed transparent action strips into the 768px desktop-pet pack."""
from pathlib import Path
import json
from collections import deque
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
STRIPS = ROOT / "artwork" / "remaining_actions" / "transparent"
CHARACTER = ROOT / "assets" / "characters" / "main_character"
REPORT = ROOT / "reports" / "remaining_actions_import.json"
SPECS = {"sit": 8, "sleep": 8, "surprised": 6, "dragged": 6, "fall": 8}
CANVAS = (768, 768)
MAX_HEIGHT = 680
BOTTOM_MARGIN = 20


def keep_largest_component(image: Image.Image) -> Image.Image:
    """Remove neighboring-slot fragments while preserving the connected character."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    width, height = rgba.size
    mask = bytearray(1 if value > 16 else 0 for value in alpha.getdata())
    seen = bytearray(width * height)
    largest: list[int] = []
    for start, visible in enumerate(mask):
        if not visible or seen[start]:
            continue
        seen[start] = 1
        queue = deque([start])
        component = []
        while queue:
            current = queue.popleft()
            component.append(current)
            x, y = current % width, current // width
            for neighbor in (current - 1, current + 1, current - width, current + width):
                if neighbor < 0 or neighbor >= width * height or seen[neighbor] or not mask[neighbor]:
                    continue
                nx, ny = neighbor % width, neighbor // width
                if abs(nx - x) + abs(ny - y) != 1:
                    continue
                seen[neighbor] = 1
                queue.append(neighbor)
        if len(component) > len(largest):
            largest = component
    if not largest:
        raise ValueError("No visible component")
    keep = bytearray(width * height)
    for index in largest:
        keep[index] = 1
    pixels = list(rgba.getdata())
    cleaned = [pixel if keep[index] else (0, 0, 0, 0) for index, pixel in enumerate(pixels)]
    rgba.putdata(cleaned)
    return rgba


def split_strip(path: Path, count: int, action: str) -> list[Image.Image]:
    with Image.open(path) as opened:
        strip = opened.convert("RGBA")
    edges = [round(index * strip.width / count) for index in range(count + 1)]
    frames = [keep_largest_component(strip.crop((edges[i], 0, edges[i + 1], strip.height))) for i in range(count)]
    boxes = [frame.getchannel("A").getbbox() for frame in frames]
    if any(box is None for box in boxes):
        raise ValueError(f"Blank slot in {path}")
    heights = [box[3] - box[1] for box in boxes if box]
    shared_scale = min(1.0, MAX_HEIGHT / max(heights))
    source_bottom = max(box[3] for box in boxes if box)
    results = []
    for frame, box in zip(frames, boxes):
        sprite = frame.crop(box)
        if shared_scale != 1.0:
            size = (max(1, round(sprite.width * shared_scale)), max(1, round(sprite.height * shared_scale)))
            sprite = sprite.resize(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        x = (CANVAS[0] - sprite.width) // 2
        if action == "fall":
            bottom = CANVAS[1] - BOTTOM_MARGIN - round((source_bottom - box[3]) * shared_scale)
        elif action == "dragged":
            bottom = 620 - round((source_bottom - box[3]) * shared_scale)
        else:
            bottom = CANVAS[1] - BOTTOM_MARGIN
        y = bottom - sprite.height
        canvas.alpha_composite(sprite, (x, y))
        results.append(canvas)
    return results


def main() -> int:
    imported = {}
    for action, count in SPECS.items():
        source = STRIPS / f"{action}.png"
        frames = split_strip(source, count, action)
        target = CHARACTER / action
        target.mkdir(parents=True, exist_ok=True)
        for old in target.glob("*.png"):
            old.unlink()
        for index, frame in enumerate(frames, 1):
            frame.save(target / f"{index:03}.png", optimize=True)
        imported[action] = len(frames)

    config_path = CHARACTER / "character.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config.update({"name": "ZhangLe", "version": "1.0.0", "placeholder": False})
    status = {name: "generated_reviewed" for name in config["animations"]}
    config["asset_status"] = status
    for name, animation in config["animations"].items():
        animation["placeholder"] = False
        animation["asset_status"] = "generated_reviewed"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"ok": True, "imported": imported}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
