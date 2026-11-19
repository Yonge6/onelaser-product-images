"""Render index.html from images.json + tools/index.tpl.html.

Never touches images/ or thumbs/. images.json is the source of truth.
ZIP sizes come from tools/zips.json (written by tools/make_zips.sh).
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER, NAME = "Yonge6", "onelaser-product-images"
RAWBASE = f"https://raw.githubusercontent.com/{OWNER}/{NAME}/main/"

data = json.load(open(os.path.join(ROOT, "images.json"), encoding="utf-8"))
zips = json.load(open(os.path.join(ROOT, "tools", "zips.json"), encoding="utf-8"))
rel = zips["release"]
dl = f"https://github.com/{OWNER}/{NAME}/releases/download/{rel}/"

for g in data:
    z = zips["files"].get(f"onelaser-{g['slug']}.zip")
    if z:
        g["zip"], g["zipmb"] = dl + f"onelaser-{g['slug']}.zip", z

allz = zips["files"]["onelaser-all-images.zip"]
tpl = open(os.path.join(ROOT, "tools", "index.tpl.html"), encoding="utf-8").read()
page = (tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
        .replace("__RAWBASE__", RAWBASE)
        .replace("__ALLZIP__", dl + "onelaser-all-images.zip")
        .replace("__ALLZIPMB__", str(allz))
        .replace("__DATE__", rel.lstrip("v").replace(".", "-")))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(page)
print("rendered", sum(len(g["items"]) for g in data), "images in", len(data), "groups")
