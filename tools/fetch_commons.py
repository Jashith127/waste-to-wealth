"""Fetch openly licensed reference photos from Wikimedia Commons.

Usage: python tools/fetch_commons.py "Category:Russell Market, Bangalore" [more categories...]

Writes 1280px copies to field/external/commons/ and appends licence + credit
for each file to field/external/commons/credits.json. Re-runnable: files that
already exist are skipped.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
OUT = Path(__file__).resolve().parent.parent / "field" / "external" / "commons"
UA = "WasteToWealthGame/0.1 (student design project; reference gathering)"


def api(params):
    params = {**params, "format": "json"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def category_files(cat):
    data = api({
        "action": "query", "generator": "categorymembers", "gcmtitle": cat,
        "gcmtype": "file", "gcmlimit": "100", "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": "1280",
    })
    return list(data.get("query", {}).get("pages", {}).values())


def main(cats):
    OUT.mkdir(parents=True, exist_ok=True)
    credits_path = OUT / "credits.json"
    credits = json.loads(credits_path.read_text(encoding="utf-8")) if credits_path.exists() else {}
    for cat in cats:
        for page in category_files(cat):
            info = page["imageinfo"][0]
            meta = info.get("extmetadata", {})
            lic = meta.get("LicenseShortName", {}).get("value", "")
            if not re.search(r"CC|Public domain|PD", lic, re.I):
                print("skip (licence)", page["title"], lic)
                continue
            name = re.sub(r"[^A-Za-z0-9._-]+", "_", page["title"].removeprefix("File:"))
            name = Path(name).stem[:80] + ".jpg"
            dest = OUT / name
            if not dest.exists():
                req = urllib.request.Request(info["thumburl"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=120) as r:
                    dest.write_bytes(r.read())
            credits[name] = {
                "title": page["title"],
                "page": info["descriptionurl"],
                "licence": lic,
                "artist": strip_html(meta.get("Artist", {}).get("value")),
                "date": strip_html(meta.get("DateTimeOriginal", {}).get("value")),
                "category": cat,
            }
            print("ok", name, "|", lic)
    credits_path.write_text(json.dumps(credits, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
