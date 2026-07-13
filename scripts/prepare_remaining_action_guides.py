"""Create deterministic slot-only guides for remaining generated action strips."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artwork" / "remaining_actions" / "layout_guides"
SPECS = {"sit": 8, "sleep": 8, "surprised": 6, "dragged": 6, "fall": 8}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    width, height = 1536, 768
    for name, count in SPECS.items():
        image = Image.new("RGB", (width, height), "#00FFFF")
        draw = ImageDraw.Draw(image)
        slot = width / count
        for index in range(count):
            left = round(index * slot + 10)
            right = round((index + 1) * slot - 10)
            draw.rectangle((left, 28, right, height - 28), outline="#007777", width=3)
            cx = (left + right) // 2
            draw.line((cx, 60, cx, height - 60), fill="#40BEBE", width=1)
        image.save(OUT / f"{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
