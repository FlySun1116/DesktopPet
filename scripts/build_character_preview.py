from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]; CHAR = ROOT / "assets" / "characters" / "main_character"


def main():
    actions = ["idle","walk","sit","sleep","wave","happy","surprised","dragged","fall"]
    board = Image.new("RGBA", (900, 900), (245, 247, 252, 255)); draw = ImageDraw.Draw(board)
    for i, action in enumerate(actions):
        with Image.open(CHAR/action/"001.png") as im: thumb = im.convert("RGBA"); thumb.thumbnail((260,240)); x=(i%3)*300+20; y=(i//3)*280+60; board.alpha_composite(thumb,(x+(260-thumb.width)//2,y)); draw.text((x+10,y+240),f"PLACEHOLDER · {action}",fill=(200,30,60,255))
    board.save(CHAR/"preview.png"); print(CHAR/"preview.png")


if __name__ == "__main__": main()
