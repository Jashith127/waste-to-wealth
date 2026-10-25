"""Pack a station's Blender renders for Phaser.

Usage: python tools/pack_layers.py s01

Reads art/build/renders/<id>/*.png (+ anchors.json) and writes to public/assets/stations/<id>/:
  bg.png              the full-frame background (fridge light off)
  fx_fridge_glow.png  only the pixels that change when the fridge light is on (overlay)
  <sprite>.png        every other layer, cropped to its visible pixels
  pack.json           Phaser asset pack (keys "<id>_<layer>")
  layers.json         where each layer sits in the 1920x1080 frame, plus anchors
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
FRAME = (1920, 1080)
PAD = 2


def crop_to_alpha(im, floor=6):
    """Crop to pixels with alpha above `floor` (denoised transparent film leaves faint alpha everywhere)."""
    box = im.getchannel("A").point(lambda a: 255 if a > floor else 0).getbbox()
    if not box:
        return None, None
    x0, y0, x1, y1 = box
    box = (max(x0 - PAD, 0), max(y0 - PAD, 0), min(x1 + PAD, im.width), min(y1 + PAD, im.height))
    return im.crop(box), box


def glow_overlay(on, off, noise=10, gain=8):
    """Alpha = how much each pixel changes beyond render noise, so `overlay` over `off` ~ `on`."""
    diff = ImageChops.difference(on.convert("RGB"), off.convert("RGB")).convert("L")
    alpha = diff.point(lambda v: 0 if v <= noise else min(255, (v - noise) * gain))
    overlay = on.copy()
    overlay.putalpha(ImageChops.multiply(alpha, on.getchannel("A")))
    return crop_to_alpha(overlay)


def main(station):
    src = ROOT / "art" / "build" / "renders" / station
    out = ROOT / "public" / "assets" / "stations" / station
    out.mkdir(parents=True, exist_ok=True)
    layers, files = {}, []

    def emit(name, im, box):
        path = out / f"{name}.png"
        im.save(path, optimize=True)
        layers[name] = {"x": box[0], "y": box[1], "w": im.width, "h": im.height}
        files.append({"type": "image", "key": f"{station}_{name}", "url": f"assets/stations/{station}/{name}.png"})
        print(f"{name:16} {im.width}x{im.height} at {box[0]},{box[1]}  {path.stat().st_size // 1024} KB")

    off = Image.open(src / "bg_fridge_off.png").convert("RGBA")
    on = Image.open(src / "bg_fridge_on.png").convert("RGBA")
    emit("bg", off, (0, 0))
    glow, box = glow_overlay(on, off)
    if glow:
        emit("fx_fridge_glow", glow, box)

    anchors = json.loads((src / "anchors.json").read_text(encoding="utf-8"))
    for png in sorted(src.glob("*.png")):
        if png.stem.startswith("bg_"):
            continue
        im = Image.open(png).convert("RGBA")
        if png.stem.endswith("_shadow"):   # a contact shadow lives near its prop: clear stray catcher alpha
            cx, cy = anchors[png.stem.removesuffix("_shadow") + "_centre"]
            keep = Image.new("L", im.size, 0)
            keep.paste(255, (int(cx - 170), int(cy - 70), int(cx + 170), int(cy + 90)))
            im.putalpha(ImageChops.multiply(im.getchannel("A"), keep))
        im, box = crop_to_alpha(im)
        if im:
            emit(png.stem, im, box)

    (out / "layers.json").write_text(json.dumps({"frame": FRAME, "layers": layers, "anchors": anchors}, indent=2), encoding="utf-8")
    (out / "pack.json").write_text(json.dumps({station: {"files": files}}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
