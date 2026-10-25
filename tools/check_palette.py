"""Art-bible §3.3 rule 1: no environment surface within ΔE (CIE76) 20 of a meaning colour.

Usage: python tools/check_palette.py [station ...]     (default: every station in public/assets/stations)

Checks every shipped layer PNG. Fails (exit 1) if more than LIMIT of a layer's opaque pixels
sit within ΔE 20 of cost red, income green, pay saffron or off-site blue.
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MEANING = {"cost": "#C42B20", "income": "#2E6B34", "pay": "#F0A31F", "offsite": "#1F5BA8"}
THRESHOLD = 20.0
LIMIT = 0.002          # 0.2% of opaque pixels
STEP = 3               # sample every 3rd pixel each way

# Layers that carry a meaning colour on purpose (art bible §3.2), with the share each may use.
ALLOW = {
    "s03/crate.png": {"offsite": 1.0},                    # task 14: the sealed crate is Chamber B blue
    "s04/crate.png": {"offsite": 1.0},                    # the same crate, going into Chamber B
    "s04/bg.png": {"income": 0.01, "offsite": 0.01},     # Chamber A/B door bands (lead, 2026-10-25); Phaser adds the words
    "s04/fx_chamber_light_night.png": {"income": 0.03, "offsite": 0.03},   # the same bands, lit by the chamber windows
}


def lab(rgb):
    c = [v / 255 for v in rgb]
    c = [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c]
    x = (0.4124 * c[0] + 0.3576 * c[1] + 0.1805 * c[2]) / 0.95047
    y = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    z = (0.0193 * c[0] + 0.1192 * c[1] + 0.9505 * c[2]) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


MEANING_LAB = {k: lab(tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))) for k, v in MEANING.items()}


def check(png, allow=None):
    im = Image.open(png).convert("RGBA")
    px = im.load()
    total, hits = 0, {k: 0 for k in MEANING}
    cache = {}
    for yy in range(0, im.height, STEP):
        for xx in range(0, im.width, STEP):
            r, g, b, a = px[xx, yy]
            if a < 200:
                continue
            total += 1
            key = (r >> 2, g >> 2, b >> 2)
            if key not in cache:
                L = lab((r, g, b))
                cache[key] = next((k for k, m in MEANING_LAB.items()
                                   if sum((p - q) ** 2 for p, q in zip(L, m)) ** 0.5 < THRESHOLD), None)
            if cache[key]:
                hits[cache[key]] += 1
    share = {k: v / total for k, v in hits.items() if total and v}
    bad = {k: v for k, v in share.items() if v > (allow or {}).get(k, LIMIT)}
    return total, share, bad


def main(stations):
    base = ROOT / "public" / "assets" / "stations"
    stations = stations or sorted(p.name for p in base.iterdir() if p.is_dir())
    failed = False
    for st in stations:
        for png in sorted((base / st).glob("*.png")):
            total, share, bad = check(png, ALLOW.get(f"{st}/{png.name}"))
            note = ", ".join(f"{k} {v:.2%}" for k, v in share.items()) or "clean"
            print(f"{'FAIL' if bad else 'ok  '} {st}/{png.name:20} {note}")
            failed |= bool(bad)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
