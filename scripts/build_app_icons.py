from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


def main() -> None:
    parser = argparse.ArgumentParser(description="Build application icons from a square source image.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("assets/app_icon"))
    args = parser.parse_args()

    with Image.open(args.source) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        side = min(image.size)
        left = (image.width - side) // 2
        top = (image.height - side) // 2
        image = image.crop((left, top, left + side, top + side))
        image = image.resize((512, 512), Image.Resampling.LANCZOS)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    image.save(args.output_dir / "app_icon.png", optimize=True)
    image.save(
        args.output_dir / "app_icon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
