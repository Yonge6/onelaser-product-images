# AGENTS.md — rules for anyone editing this repo (Codex, Claude, people)

This repo is the OneLaser product image library, published at
https://yonge6.github.io/onelaser-product-images/ by `.github/workflows/build.yml` on every push to `main`.

## What to edit

| You want to… | Edit | Don't touch |
|---|---|---|
| Add / replace / remove images | `images/<series>/` and the matching entry in `images.json` | `index.html` |
| Rename an image, change its display name, model or order | `images.json` (and `git mv` the file) | |
| Add a model filter (like Hydra 7/9/13/16) | `"modelFilters": [..]` on the series in `images.json`, `"model": N` on each item | |
| Change page layout, text, translations | `tools/index.tpl.html` (zh + en strings live in the `T` object) | `index.html` |

`index.html` is **generated** by `tools/render.py` in CI. Edits to it are overwritten on the next push.

## images.json conventions

- One object per series: `group` (display name), `title`, `slug` (= folder name under `images/`), `items`, optional `modelFilters`.
- Item: `name` (Chinese or English display name), `file` (`images/<slug>/<file>`), `thumb` (`thumbs/<slug>/<stem>.jpg`), `w`, `h`, `kb`, optional `model` (number).
- File names: `<slug>-<model>-NNN.ext` when the model is known (e.g. `cobra-8-001.png`), else `<slug>-NNN.ext`.
- `w`, `h`, `kb` and the thumbnail may be omitted; CI measures and generates them. A file in `images/<slug>/` that is missing from `images.json` is still published (appended to its series), but please list it.
- Keep filenames stable once published: other people paste the raw links
  (`https://raw.githubusercontent.com/Yonge6/onelaser-product-images/main/images/...`) into the website and ad tools.
  If you must rename, mention the old → new names in the commit message.

## Before pushing

- `git pull --rebase` first: more than one agent pushes to `main`.
- Optional local check: `python3 tools/render.py` (needs Pillow for thumbnails) — exit code 1 means `images.json` points at a missing file.
- Single files must stay under 100 MB (GitHub limit).

## ZIP downloads

`tools/ci_zips.sh` (run by CI) re-zips only the series whose images changed and uploads them to the rolling
release `images-latest`, so download links stay the same. Don't create other releases for this.
