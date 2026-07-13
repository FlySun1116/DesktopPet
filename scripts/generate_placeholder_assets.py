"""Generate clearly labelled placeholder animation assets.

These files are development stand-ins and must never be presented as final artwork.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CHAR_ROOT = ROOT / "assets" / "characters" / "main_character"
SHEET_ROOT = ROOT / "artwork" / "character_sheet"
CANVAS = 768
ANIMATIONS = {
    "idle": (8, 7, True), "walk": (10, 10, True), "sit": (8, 8, False),
    "sleep": (8, 5, True), "wave": (8, 9, False), "happy": (8, 10, False),
    "surprised": (6, 10, False), "dragged": (6, 6, True), "fall": (8, 12, False),
}


def font(size: int):
    for path in ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/msyhbd.ttc"]:
        if Path(path).exists(): return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_character(action: str, index: int, count: int) -> Image.Image:
    im = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    phase = index / count * 6.283
    bounce = round(8 * __import__("math").sin(phase)) if action in ("idle", "walk", "happy") else 0
    cx, floor = 384, 680
    if action == "dragged": floor -= 75
    if action == "sleep": floor += 15
    # Deliberately generic mascot silhouette, not an attempted likeness.
    d.ellipse((cx-116, floor-455+bounce, cx+116, floor-223+bounce), fill=(125, 180, 244, 255), outline=(40, 70, 110, 255), width=10)
    d.rounded_rectangle((cx-100, floor-255+bounce, cx+100, floor-75+bounce), 55, fill=(250, 184, 206, 255), outline=(80, 60, 90, 255), width=10)
    d.ellipse((cx-68, floor-370+bounce, cx-43, floor-345+bounce), fill=(30, 40, 65, 255)); d.ellipse((cx+43, floor-370+bounce, cx+68, floor-345+bounce), fill=(30, 40, 65, 255))
    leg_shift = round(24 * __import__("math").sin(phase)) if action == "walk" else 0
    d.line((cx-45, floor-90, cx-55-leg_shift, floor), fill=(70, 70, 100, 255), width=35); d.line((cx+45, floor-90, cx+55+leg_shift, floor), fill=(70, 70, 100, 255), width=35)
    arm = -70 if action == "wave" and index % 3 else 25
    d.line((cx+85, floor-230, cx+165, floor-240+arm), fill=(250, 184, 206, 255), width=32)
    d.text((cx, 56), "PLACEHOLDER", font=font(42), anchor="ma", fill=(230, 35, 70, 245), stroke_width=2, stroke_fill="white")
    d.text((cx, 110), f"{action.upper()} {index+1:03}/{count:03}", font=font(25), anchor="ma", fill=(50, 50, 65, 240))
    return im


def make_sheet(name: str, subtitle: str):
    im = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((50, 130, 718, 650), 35, fill=(235, 242, 252, 230), outline=(220, 35, 70, 255), width=8)
    d.text((384, 230), "PLACEHOLDER", font=font(62), anchor="mm", fill=(220, 35, 70, 255))
    d.text((384, 340), name, font=font(35), anchor="mm", fill=(35, 55, 85, 255))
    d.multiline_text((384, 455), subtitle, font=font(24), anchor="mm", align="center", fill=(55, 65, 80, 255), spacing=10)
    im.save(SHEET_ROOT / name)


def main():
    CHAR_ROOT.mkdir(parents=True, exist_ok=True); SHEET_ROOT.mkdir(parents=True, exist_ok=True)
    metadata = {"id":"main_character", "name":"Main Character (PLACEHOLDER)", "version":"0.1.0-placeholder", "placeholder":True, "canvas_size":[CANVAS,CANVAS], "anchor":"bottom_center", "default_scale":0.36, "animations":{}}
    for action, (count, fps, loop) in ANIMATIONS.items():
        folder = CHAR_ROOT / action; folder.mkdir(exist_ok=True)
        for old in folder.glob("*.png"): old.unlink()
        for i in range(count): draw_character(action, i, count).save(folder / f"{i+1:03}.png")
        metadata["animations"][action] = {"folder":action, "fps":fps, "loop":loop, "placeholder":True}
    (CHAR_ROOT / "character.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    draw_character("preview", 0, 1).save(CHAR_ROOT / "preview.png")
    sheets = ["character_front.png","character_left_45.png","character_right_45.png","character_side.png","character_back.png","character_expressions.png","character_palette.png","character_sheet.png"]
    for name in sheets: make_sheet(name, "Temporary development asset\nReplace with approved character artwork")
    print(f"Generated {sum(v[0] for v in ANIMATIONS.values())} placeholder frames")


if __name__ == "__main__": main()
