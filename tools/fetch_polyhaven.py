"""Fetch CC0 models from Poly Haven for set dressing (art bible §0, Tier B2: generic objects only).

Usage: python tools/fetch_polyhaven.py            # every model in MODELS, 1k glTF
Writes art/external/polyhaven/<id>/... and art/external/polyhaven/credits.json. Existing files are
kept. The model files are not committed (.gitignore); this script re-fetches them. Approved by
the lead on 2026-10-25 (21 models, about 68 MB).
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "art" / "external" / "polyhaven"
MODELS = {
    # the back-lane pile (s02)
    "trashbag": "pile", "compost_bags": "pile", "cement_bag": "pile", "cardboard_box_01": "pile",
    "street_rat": "pile", "water_manhole_cover": "pile",
    # the street (s02, s03, s05)
    "plastic_monobloc_chair_01": "street", "plastic_crate_01": "street", "plastic_crate_03": "street",
    "wooden_crate_01": "street", "wicker_basket_01": "street", "Barrel_01": "street", "metal_trash_can": "street",
    "small_lpg_tank": "street", "modular_electricity_poles": "street", "modular_electric_cables": "street",
    # the hub (s03-s05)
    "hand_truck": "hub", "steel_frame_shelves_01": "hub", "garden_hose_wall_mounted_01": "hub",
    "portable_generator": "hub", "plastic_jerrycan": "hub",
}
UA = {"User-Agent": "waste-to-wealth-fetch/1.0"}


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def download(url, dest):
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        dest.write_bytes(r.read())


def main():
    credits = {}
    for mid, use in MODELS.items():
        files = get_json(f"https://api.polyhaven.com/files/{mid}")["gltf"]["1k"]["gltf"]
        folder = OUT / mid
        download(files["url"], folder / Path(files["url"]).name)
        for rel, inc in files.get("include", {}).items():
            download(inc["url"], folder / rel)
        info = get_json(f"https://api.polyhaven.com/info/{mid}")
        credits[mid] = {"name": info.get("name"), "authors": list(info.get("authors", {})), "licence": "CC0",
                        "source": f"https://polyhaven.com/a/{mid}", "use": use, "gltf": f"{mid}/{Path(files['url']).name}"}
        print(f"{mid:30} ok")
    (OUT / "credits.json").write_text(json.dumps(credits, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
