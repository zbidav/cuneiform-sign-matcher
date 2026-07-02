# Cuneiform Sign Matcher

Draw an unknown cuneiform sign — as straight strokes — and get back a ranked list of
candidate signs to help identify it. Built for Assyriologists who currently match signs
by hand against paper sign-lists or a slow text search on
[eBL](https://www.ebl.lmu.de/signs).

**Live app:** open `docs/index.html` (works offline) or serve `docs/` on GitHub Pages.

---

## How it works

The whole app is one self-contained page (`docs/index.html`) — no build step, no server,
no network calls. It runs the same way opened from disk or hosted.

- **Input.** Draw with the **Line** tool (press-drag-release → one straight segment) or
  **Freehand** (a freehand path is auto-straightened into a few line segments via
  Ramer–Douglas–Peucker). Cuneiform is mostly straight strokes, so straight lines stay
  straight — that's the point.
- **Reference signs.** All 879 signs of the Unicode Cuneiform block, stored as **vector
  outlines** (`docs/js/signs-data.js`) extracted offline from the Noto Sans Cuneiform font.
- **Matching.** Your drawing and each sign are normalized to a unit box and turned into
  evenly spaced point clouds; candidates are ranked by a symmetric **chamfer distance**.
  Results render as vector glyphs and link out to the eBL sign list.

Verified: a drawn **vertical** line ranks **U+12079 (DIŠ, the vertical wedge)** first; a
**horizontal** line ranks **U+12030 (AŠ, the horizontal wedge)** first; every sign matched
against itself ranks #1.

---

## Run / deploy

```bash
# open directly
xdg-open docs/index.html

# or serve (same as GitHub Pages)
cd docs && python3 -m http.server 8000   # -> http://localhost:8000
```

GitHub Pages: serve from the `/docs` folder on the default branch.

---

## Roadmap

**Now — geometric matcher (this repo).** Vector chamfer matching. Fast, honest, offline.
Good for clearly-drawn signs; will confuse dense, visually-similar sign families.

**Next — the eBL embedding (`model/`).** Reuse
[`sign-embedding`](https://github.com/ElectronicBabylonianLiterature/sign-embedding)
(PyTorch ResNet-18 → 512-dim vectors), fine-tune toward sketches, export to ONNX, and run
it in-browser via `onnxruntime-web` — same UI, smarter matcher. Note: eBL publishes **no
checkpoint** (trains from scratch), and its data is sign *photos*, so a freehand sketch is
out-of-distribution and needs sketch-oriented augmentation. Details in `model/README.md`.

**Also planned.** Map Unicode codepoints → MZL/ABZ/eBL sign IDs; scope which period(s) to
prioritize with the Assyriologists; optionally pull line-art references from eBL directly.

## Regenerate the vector data

```bash
python3 tools/extract_signs.py   # rebuilds docs/js/signs-data.js from the bundled font
```

## Layout

```
docs/
  index.html        the entire app (drawing + matcher + UI)
  js/signs-data.js  879 signs as vector outlines (generated)
  fonts/            bundled Noto Sans Cuneiform (OFL) — provenance of signs-data.js
tools/extract_signs.py   font -> vector data generator
model/            future embedding-model pipeline
cuneiform-sign-matcher-plan.md   original research + phased plan
```
