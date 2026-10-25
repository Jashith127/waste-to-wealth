"""Fetch OpenStreetMap footprints around Russell Market for set layout.

Usage: python tools/fetch_osm.py

Saves the raw Overpass response to field/external/osm/russell-market-area.json
and prints each feature's size in metres. Data (c) OpenStreetMap contributors, ODbL.
"""
import json
import math
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
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
