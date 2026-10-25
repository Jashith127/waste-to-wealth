"""Fetch OpenStreetMap footprints around Russell Market for set layout.

Usage: python tools/fetch_osm.py              # named landmarks -> russell-market-area.json
       python tools/fetch_osm.py --streets    # every road and building footprint within ~500 m of
                                              # Russell Market -> shivajinagar-streets.json (the market map)

Saves the raw Overpass response to field/external/osm/russell-market-area.json
and prints each feature's size in metres. Data (c) OpenStreetMap contributors, ODbL.
"""
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "field" / "external" / "osm"
BBOX = "12.975,77.595,12.992,77.615"
QUERY = f"""[out:json][timeout:60];
(
  way["name"~"Rus+el+ Market",i]({BBOX});
  relation["name"~"Rus+el+ Market",i]({BBOX});
  way["name"~"Cockburn",i]({BBOX});
  way["name"~"Basilica|St. Mary",i]({BBOX});
  way["name"~"Broadway",i]({BBOX});
);
out tags geom;"""


STREETS_BBOX = "12.9817,77.6000,12.9910,77.6100"
STREETS_QUERY = f"""[out:json][timeout:90];
(
  way["highway"]({STREETS_BBOX});
  way["building"]({STREETS_BBOX});
);
out tags geom;"""


def streets():
    """Roads and buildings round the market, slimmed to geometry and a few tags (lead OK 2026-10-25)."""
    for server in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
        req = urllib.request.Request(server, data=urllib.parse.urlencode({"data": STREETS_QUERY}).encode(),
                                     headers={"User-Agent": "WasteToWealthGame/0.1 (student design project)"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            print(f"{server}: {e}")
    else:
        raise SystemExit("every Overpass server failed")
    keep = ("name", "highway", "building", "amenity")
    slim = {"attribution": "(c) OpenStreetMap contributors, ODbL", "bbox": STREETS_BBOX, "ways": [
        {"tags": {k: v for k, v in e.get("tags", {}).items() if k in keep},
         "geom": [[round(p["lat"], 6), round(p["lon"], 6)] for p in e["geometry"]]}
        for e in data["elements"] if e.get("geometry")]}
    path = OUT / "shivajinagar-streets.json"
    path.write_text(json.dumps(slim, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(slim['ways'])} ways -> {path.name} ({path.stat().st_size // 1024} KB)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if "--streets" in sys.argv:
        return streets()
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=urllib.parse.urlencode({"data": QUERY}).encode(),
        headers={"User-Agent": "WasteToWealthGame/0.1 (student design project)"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.load(r)
    (OUT / "russell-market-area.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    for e in data["elements"]:
        g = e.get("geometry") or []
        if not g:
            continue
        lat0 = sum(p["lat"] for p in g) / len(g)
        lon0 = sum(p["lon"] for p in g) / len(g)
        kx, ky = 111320 * math.cos(math.radians(lat0)), 110540
        xs = [p["lon"] * kx for p in g]
        ys = [p["lat"] * ky for p in g]
        length = sum(math.dist((xs[i], ys[i]), (xs[i + 1], ys[i + 1])) for i in range(len(g) - 1))
        t = e["tags"]
        kind = t.get("building") or t.get("highway") or t.get("amenity") or t.get("shop") or "?"
        print(f"{e['id']}  {t.get('name')}  [{kind}]  bbox {max(xs)-min(xs):.0f}x{max(ys)-min(ys):.0f} m  "
              f"length {length:.0f} m  centre {lat0:.5f},{lon0:.5f}")


if __name__ == "__main__":
    main()
