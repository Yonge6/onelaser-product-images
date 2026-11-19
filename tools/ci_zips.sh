#!/bin/bash
# Refresh per-series ZIPs on the rolling release `images-latest`.
# Usage: tools/ci_zips.sh all            -> rebuild every series + all-images
#        tools/ci_zips.sh xrf cobra      -> rebuild only those series + all-images
# Needs: gh (GH_TOKEN), zip. Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="Yonge6/onelaser-product-images"
TAG="images-latest"
OUT="$(mktemp -d)"

if ! gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then
  gh release create "$TAG" -R "$REPO" --title "OneLaser 产品图 ZIP（自动更新）" \
    --notes "每次图片有变动时自动重新打包。Rebuilt automatically whenever images change. Preview: https://yonge6.github.io/onelaser-product-images/"
  set -- all
fi

if [ "${1:-}" = "all" ]; then
  series=$(ls images)
else
  series="$*"
fi

for s in $series; do
  if [ -d "images/$s" ]; then
    (cd images && zip -0 -qr "$OUT/onelaser-$s.zip" "$s")
    echo "zipped $s ($(du -h "$OUT/onelaser-$s.zip" | cut -f1))"
  else
    echo "series $s removed; deleting its zip"
    gh release delete-asset "$TAG" "onelaser-$s.zip" -R "$REPO" -y || true
  fi
done
(cd images && zip -0 -qr "$OUT/onelaser-all-images.zip" .)
gh release upload "$TAG" "$OUT"/onelaser-*.zip -R "$REPO" --clobber
rm -rf "$OUT"
