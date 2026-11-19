#!/bin/bash
# Build one ZIP per machine folder + one with everything, upload to a GitHub release,
# and record sizes in tools/zips.json. Usage: tools/make_zips.sh v2026.11.19b
set -euo pipefail
REL="${1:?release tag}"
cd "$(dirname "$0")/.."
OUT="raw/zips-$REL"
mkdir -p "$OUT"
for d in images/*/; do
  s=$(basename "$d")
  [ -f "$OUT/onelaser-$s.zip" ] || (cd images && zip -0 -qr "../$OUT/onelaser-$s.zip" "$s")
done
[ -f "$OUT/onelaser-all-images.zip" ] || (cd images && zip -0 -qr "../$OUT/onelaser-all-images.zip" .)
python3 - "$OUT" "$REL" > tools/zips.json <<'PY'
import os, sys, json
out, rel = sys.argv[1], sys.argv[2]
print(json.dumps({"release": rel, "files": {f: round(os.path.getsize(os.path.join(out, f)) / 1048576) for f in sorted(os.listdir(out)) if f.endswith(".zip")}}, indent=1))
PY
gh release create "$REL" "$OUT"/onelaser-*.zip -R Yonge6/onelaser-product-images \
  --title "OneLaser 产品图 $REL" \
  --notes "按机型打包的原图 ZIP / Original images zipped per machine. Preview: https://yonge6.github.io/onelaser-product-images/"
