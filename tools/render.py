"""Render index.html from images.json + tools/index.tpl.html.

Safe to run on every push (CI does). It never renames, moves or deletes images.
  * images.json is the source of truth for order, names, models and filters.
  * Files in images/<series>/ that images.json doesn't list are still shown (appended to that series).
  * Missing w/h/kb are measured; missing thumbnails are generated into thumbs/ (needs Pillow).
  * ZIP links point at the rolling release `images-latest`; sizes come from tools/zips.json if present,
    otherwise from the GitHub API (gh CLI), otherwise the ZIP buttons are hidden.
Writes index.html and prints a short report. Exit code 1 only if images.json references a missing file.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER, NAME = "Yonge6", "onelaser-product-images"
RAWBASE = f"https://raw.githubusercontent.com/{OWNER}/{NAME}/main/"
RELEASE = "images-latest"
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif")

try:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
except ImportError:
    Image = None

def p(*a): return os.path.join(ROOT, *a)

data = json.load(open(p("images.json"), encoding="utf-8"))
report = {"thumbs_made": [], "measured": [], "unlisted_added": [], "missing": []}

# 1. unlisted files on disk -> append to their series
by_slug = {g["slug"]: g for g in data}
listed = {it["file"] for g in data for it in g["items"]}
for slug in sorted(os.listdir(p("images"))):
    d = p("images", slug)
    if not os.path.isdir(d):
        continue
    g = by_slug.get(slug)
    if g is None:
        g = {"group": slug.replace("-", " ").title(), "title": slug.replace("-", " ").title(), "slug": slug, "items": []}
        data.append(g); by_slug[slug] = g
    for fn in sorted(os.listdir(d)):
        rel = f"images/{slug}/{fn}"
        if fn.lower().endswith(IMG_EXT) and rel not in listed:
            stem = os.path.splitext(fn)[0]
            m = re.match(rf"{re.escape(slug)}-(\d+)-\d{{3}}$", stem)
            item = {"name": stem, "file": rel, "thumb": f"thumbs/{slug}/{stem}.jpg"}
            if m:
                item["model"] = int(m.group(1))
            g["items"].append(item)
            report["unlisted_added"].append(rel)

# 2. check files, measure, thumbnail
for g in data:
    keep = []
    for it in g["items"]:
        src = p(it["file"])
        if not os.path.exists(src):
            report["missing"].append(it["file"])
            continue
        it.setdefault("thumb", "thumbs/" + it["file"].split("/", 1)[1].rsplit(".", 1)[0] + ".jpg")
        if "kb" not in it:
            it["kb"] = os.path.getsize(src) // 1024
        need_dims = not it.get("w") or not it.get("h")
        need_thumb = not os.path.exists(p(it["thumb"]))
        if (need_dims or need_thumb) and Image:
            with Image.open(src) as im:
                it["w"], it["h"] = im.size
                if need_thumb:
                    os.makedirs(os.path.dirname(p(it["thumb"])), exist_ok=True)
                    t = im.convert("RGBA")
                    bg = Image.new("RGB", t.size, (255, 255, 255)); bg.paste(t, mask=t.split()[3])
                    bg.thumbnail((640, 640)); bg.save(p(it["thumb"]), "JPEG", quality=78, optimize=True)
                    report["thumbs_made"].append(it["thumb"])
            if need_dims:
                report["measured"].append(it["file"])
        keep.append(it)
    g["items"] = keep

# 3. zip sizes
zips = {}
if os.path.exists(p("tools", "zips.json")):
    zips = json.load(open(p("tools", "zips.json")))["files"]
else:
    try:
        out = subprocess.run(["gh", "release", "view", RELEASE, "-R", f"{OWNER}/{NAME}", "--json", "assets"],
                             capture_output=True, text=True, check=True).stdout
        zips = {a["name"]: round(a["size"] / 1048576) for a in json.loads(out)["assets"]}
    except Exception as e:
        print("note: no zip sizes:", e, file=sys.stderr)
dl = f"https://github.com/{OWNER}/{NAME}/releases/download/{RELEASE}/"
for g in data:
    z = zips.get(f"onelaser-{g['slug']}.zip")
    if z is not None:
        g["zip"], g["zipmb"] = dl + f"onelaser-{g['slug']}.zip", z

# 4. render
tpl = open(p("tools", "index.tpl.html"), encoding="utf-8").read()
allz = zips.get("onelaser-all-images.zip")
date = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%cs"], capture_output=True, text=True).stdout.strip()
page = (tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
        .replace("__RAWBASE__", RAWBASE)
        .replace("__ALLZIP__", dl + "onelaser-all-images.zip" if allz is not None else "#")
        .replace("__ALLZIPMB__", str(allz if allz is not None else "–"))
        .replace("__DATE__", date))
open(p("index.html"), "w", encoding="utf-8").write(page)

print(f"rendered {sum(len(g['items']) for g in data)} images in {len(data)} groups")
for k, v in report.items():
    if v:
        print(f"  {k}: {len(v)}", *v[:20], sep="\n    ")
sys.exit(1 if report["missing"] else 0)
