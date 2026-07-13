from PIL import Image


def test_rgba_image_has_real_transparency(tmp_path):
    path = tmp_path / "frame.png"
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    image.putpixel((4, 4), (255, 0, 0, 255))
    image.save(path)
    loaded = Image.open(path)
    alpha = loaded.getchannel("A")
    lo, hi = alpha.getextrema()
    assert loaded.mode == "RGBA"
    assert lo == 0 and hi == 255


def test_rgb_image_is_not_transparent(tmp_path):
    path = tmp_path / "fake.png"
    Image.new("RGB", (8, 8), "white").save(path)
    loaded = Image.open(path)
    assert "A" not in loaded.getbands()
