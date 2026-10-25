"""Composite rendered layers over the charcoal void for a quick look (not shipped).
Usage: python tools/preview_comp.py s01 out.png layer [layer ...]"""
import sys
from PIL import Image

station, out, layers = sys.argv[1], sys.argv[2], sys.argv[3:]
canvas = Image.new("RGBA", (1920, 1080), (28, 23, 20, 255))
for name in layers:
    canvas.alpha_composite(Image.open(f"art/build/renders/{station}/{name}.png").convert("RGBA"))
canvas.convert("RGB").save(out)
