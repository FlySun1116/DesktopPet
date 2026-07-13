"""Build a review sheet for the five imported formal action sets."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CHARACTER = ROOT / "assets" / "characters" / "main_character"
OUTPUT = ROOT / "reports" / "remaining_actions_contact_sheet.png"
ACTIONS = ["sit", "sleep", "surprised", "dragged", "fall"]


def main() -> int:
    thumb = (192, 192)
    rows = []
    for action in ACTIONS:
        paths = sorted((CHARACTER / action).glob("*.png"))
        row = Image.new("RGBA", (thumb[0] * 8, thumb[1] + 28), (38, 38, 42, 255))
        draw = ImageDraw.Draw(row)
        draw.text((6, 6), action, fill="white")
        for index, path in enumerate(paths):
            with Image.open(path) as opened:
                frame = opened.convert("RGBA").resize(thumb, Image.Resampling.LANCZOS)
            checker = Image.new("RGBA", thumb, (235, 235, 235, 255))
            checker.alpha_composite(frame)
            row.alpha_composite(checker, (index * thumb[0], 28))
        rows.append(row)
    sheet = Image.new("RGBA", (thumb[0] * 8, (thumb[1] + 28) * len(rows)), (25, 25, 28, 255))
    for index, row in enumerate(rows):
        sheet.alpha_composite(row, (0, index * row.height))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
