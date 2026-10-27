"""Pack a station's Blender renders for Phaser.

Usage: python tools/pack_layers.py s01

Reads art/build/renders/<id>/ (written by art/scripts/render_station.py: one PNG per layer, some cropped
with an _offsets/ note, and atlas renders cut up by _atlas/ notes) and writes to
public/assets/stations/<id>/:
  bg.png              the full-frame background, every FX off
  fx_<name>.png       only the pixels that bg_fx_<name>.png changes (an overlay the game toggles)
  <sprite>.png        every other layer, cropped to its visible pixels
  pack.json           Phaser asset pack (keys "<id>_<layer>")
  layers.json         where each layer sits in the 1920x1080 frame, plus anchors
"""
import json
import shutil
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
    final = ROOT / "public" / "assets" / "stations" / station
    # write into a staging folder and swap it in at the end, so a running game never loads a
    # half-written station (it crashed on a missing layers.json mid-repack)
    out = final.with_name(station + ".packing")
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    layers, files = {}, []

    def emit(name, im, box):
        path = out / f"{name}.png"
        im.save(path, optimize=True)
        layers[name] = {"x": box[0], "y": box[1], "w": im.width, "h": im.height}
        files.append({"type": "image", "key": f"{station}_{name}", "url": f"assets/stations/{station}/{name}.png"})
        print(f"{name:16} {im.width}x{im.height} at {box[0]},{box[1]}  {path.stat().st_size // 1024} KB")

    # backgrounds: bg.png plus preset variants like bg_night.png; fx overlays diff against the bg of
    # the same preset (bg_fx_glow.png vs bg.png, bg_fx_glow_night.png vs bg_night.png)
    presets = [""] + sorted(p.stem[3:] for p in src.glob("bg_*.png") if not p.stem.startswith("bg_fx_"))
    for preset in presets:
        off = Image.open(src / f"bg{preset and '_' + preset}.png").convert("RGBA")
        emit(f"bg{preset and '_' + preset}", off, (0, 0))
        for fx in sorted(src.glob("bg_fx_*.png")):
            name = fx.stem.removeprefix("bg_")
            if (name.endswith("_" + preset) if preset else not any(name.endswith("_" + p) for p in presets if p)):
                overlay, box = glow_overlay(Image.open(fx).convert("RGBA"), off)
                if overlay:
                    emit(name, overlay, box)

    anchors = json.loads((src / "anchors.json").read_text(encoding="utf-8"))
    frame = Image.open(src / "bg.png").size

    def placed(im, at):
        """A crop put back where it sits in the frame."""
        full = Image.new("RGBA", frame, (0, 0, 0, 0))
        full.paste(im, tuple(at))
        return full

    # sprites: one PNG per layer (cropped to its render border if _offsets/ says so), or a cell of an
    # atlas render (_atlas/<name>.json: its box in the atlas, and where that box sits in the frame)
    sprites, atlases = {}, {}
    for png in sorted(src.glob("*.png")):
        if png.stem == "bg" or png.stem.startswith(("bg_", "atlas_")):
            continue
        sidecar = src / "_offsets" / f"{png.stem}.json"
        sprites[png.stem] = (png, json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else None)
    for sidecar in sorted((src / "_atlas").glob("*.json")) if (src / "_atlas").exists() else []:
        sprites[sidecar.stem] = (None, json.loads(sidecar.read_text(encoding="utf-8")))
    for stem in sorted(sprites):
        png, info = sprites[stem]
        if png is None:
            if info["atlas"] not in atlases:
                atlases[info["atlas"]] = Image.open(src / info["atlas"]).convert("RGBA")
            im = placed(atlases[info["atlas"]].crop(tuple(info["box"])), info["at"])
        else:
            im = Image.open(png).convert("RGBA")
            if info:
                im = placed(im, info)
        prop = stem.split("_shadow")[0]
        if "_shadow" in stem:              # a contact shadow lives near its prop: clear stray catcher alpha
            cx, cy = anchors[prop + "_centre"]
            dx, dy = 170, 90
            if prop + "_shadow_extent" in anchors:          # a long prop (the s02 handcart) names its far corner
                ex, ey = anchors[prop + "_shadow_extent"]
                dx, dy = max(dx, abs(ex - cx) + 80), max(dy, abs(ey - cy) + 160)
            keep = Image.new("L", im.size, 0)
            keep.paste(255, (int(cx - dx), int(cy - max(70, dy - 20)), int(cx + dx), int(cy + dy)))
            im.putalpha(ImageChops.multiply(im.getchannel("A"), keep))
        im, box = crop_to_alpha(im)
        if im:
            emit(stem, im, box)

    packed = {"frame": FRAME, "layers": layers, "anchors": anchors}
    if (src / "world.json").exists():                      # world-space data for free movement (s02)
        packed["world"] = json.loads((src / "world.json").read_text(encoding="utf-8"))
    (out / "layers.json").write_text(json.dumps(packed, indent=2), encoding="utf-8")
    (out / "pack.json").write_text(json.dumps({station: {"files": files}}, indent=2), encoding="utf-8")
    old = final.with_name(station + ".old")
    shutil.rmtree(old, ignore_errors=True)
    if final.exists():
        final.rename(old)
    out.rename(final)
    shutil.rmtree(old, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1])
