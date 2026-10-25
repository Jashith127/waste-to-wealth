"""Cut art-bible reference crops from field photos and sample their colours.

Usage: python tools/make_reference_crops.py

Reads CROPS below, writes docs/art-bible/crops/<id>.png and prints the median
colour of each crop's sample box, which docs/art-bible.md quotes as the
environment palette. Re-runnable.
"""
import json
from pathlib import Path
from statistics import median

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "field" / "photos"
OUT = ROOT / "docs" / "art-bible" / "crops"

# id: (photo, crop box, sample box inside the photo or None)
CROPS = {
    "R01-awning":         ("F04-bismillah-meat-corner.png", (0, 125, 960, 255), (300, 150, 420, 215)),
    "R02-shopfront":      ("F04-bismillah-meat-corner.png", (100, 240, 760, 960), None),
    "R03-hung-meat":      ("F04-bismillah-meat-corner.png", (110, 300, 300, 580), (150, 360, 220, 480)),
    "R04-orange-plaster": ("F04-bismillah-meat-corner.png", (100, 330, 180, 900), (112, 560, 140, 700)),
    "R05-cream-wall":     ("F04-bismillah-meat-corner.png", (690, 300, 780, 860), (705, 450, 750, 620)),
    "R06-shutter-blue":   ("F04-bismillah-meat-corner.png", (760, 260, 960, 440), (800, 300, 940, 400)),
    "R07-paving":         ("F04-bismillah-meat-corner.png", (30, 870, 720, 1034), (300, 950, 400, 1010)),
    "R08-chairs":         ("F04-bismillah-meat-corner.png", (600, 710, 930, 920), (630, 760, 690, 820)),
    "R09-interior":       ("F04-bismillah-meat-corner.png", (240, 370, 560, 630), (420, 470, 520, 520)),
    "R10-steel-kadai":    ("F05-sweet-chaat-counter.png", (580, 250, 898, 780), (640, 300, 760, 340)),
    "R11-gas-hose-floor": ("F05-sweet-chaat-counter.png", (260, 440, 720, 860), (300, 560, 380, 640)),
    "R12-red-wall":       ("F05-sweet-chaat-counter.png", (0, 0, 250, 560), (40, 100, 200, 400)),
    "R13-red-crates":     ("F03-restaurant-kitchen.png", (0, 590, 110, 1054), (10, 640, 60, 760)),
    "R14-blue-drum":      ("F03-restaurant-kitchen.png", (60, 570, 310, 1054), (120, 700, 260, 900)),
    "R15-charcoal-glow":  ("F03-restaurant-kitchen.png", (230, 220, 700, 600), (440, 470, 510, 500)),
    "R16-steel-rack":     ("F03-restaurant-kitchen.png", (580, 260, 780, 700), None),
    "R17-worn-door":      ("F03-restaurant-kitchen.png", (740, 0, 960, 1054), (850, 600, 920, 760)),
    "R18-stained-facade": ("F02-new-taj-durbar-front.png", (0, 130, 840, 250), (300, 160, 480, 220)),
    "R19-wires-pole":     ("F02-new-taj-durbar-front.png", (820, 0, 1280, 776), None),
    "R20-tarpaulin":      ("F01-falooda-cart-square.png", (590, 95, 720, 170), (620, 110, 690, 150)),
    "R21-steel-cart":     ("F01-falooda-cart-square.png", (300, 130, 720, 540), (380, 300, 460, 350)),
    "R22-minaret":        ("F01-falooda-cart-square.png", (300, 0, 760, 130), (340, 40, 400, 100)),
    # external, CC BY-SA (credits in field/external/commons/credits.json)
    "R23-facade-pink-2020":  ("../external/commons/Russel_Market_Shivaji_Nagar_Bengaluru.jpg", (0, 300, 1280, 900), (600, 700, 780, 780)),
    "R24-facade-white-2023": ("../external/commons/Russell_Market.jpg", (420, 180, 980, 900), (1000, 560, 1100, 640)),
    "R25-tiled-counter":     ("../external/commons/ST832372_2240996153_.jpg", (100, 480, 720, 960), None),
    "R26-hung-carcasses":    ("../external/commons/ST832372_2240996153_.jpg", (60, 170, 420, 640), None),
}


def median_hex(img, box):
    px = list(img.crop(box).convert("RGB").getdata())
    r, g, b = (int(median(c[i] for c in px)) for i in range(3))
    return f"#{r:02X}{g:02X}{b:02X}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    samples = {}
    for cid, (photo, box, sample) in CROPS.items():
        img = Image.open(PHOTOS / photo)
        img.crop(box).save(OUT / f"{cid}.png", optimize=True)
        if sample:
            samples[cid] = median_hex(img, sample)
    print(json.dumps(samples, indent=2))


if __name__ == "__main__":
    main()
