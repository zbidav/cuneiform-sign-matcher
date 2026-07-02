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

- **Input.** Draw with the **Line** tool (press-drag → one straight segment), **Freehand**
  (auto-straightened into segments via Ramer–Douglas–Peucker), or stamp **basal wedges**
  (vertical / horizontal / diagonal / Winkelhaken) to build a sign from primitives.
- **Reference signs.** The Unicode Cuneiform block as **vector outlines**, extracted offline
  from cuneiform fonts. Each sign carries its name and — for common signs — **MZL/ABZ
  numbers and readings** pulled from the eBL API (`tools/fetch_ebl_meta.py`).
- **Periods.** The **Period** selector swaps the whole reference set to a period-specific
  font's forms, so matching *and* the rendered candidates use authentic shapes:
  Neo-Assyrian (Assurbanipal), Old Babylonian (Santakku), Middle Babylonian (SantakkuM),
  Neo-Babylonian (Esagil), Hittite (Ullikummi), Modern (Noto). Datasets are lazy-loaded.
- **Matching.** Drawing and sign are normalized to a unit box, densified into point clouds,
  and ranked by a symmetric **chamfer distance**. Cards show name, readings, MZL, and link
  to the eBL sign page by name.

Verified: a drawn **vertical** line ranks **U+12079 (DIŠ, the vertical wedge)** first in
every period; the four wedges match distinct sign families; DIŠ's shape genuinely differs
between periods; every sign matches itself at rank #1.

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

**Also planned.** Improve the name→eBL match rate (172/879 resolve today); confirm period
font licensing for wider distribution; scope priority period(s) with the Assyriologists.

## Regenerate the data

```bash
python3 tools/extract_signs.py       # base set (Noto) -> docs/js/signs-data.js
python3 tools/fetch_ebl_meta.py      # add MZL/ABZ + readings from the eBL API (cached)
bash    tools/download_period_fonts.sh   # fetch eBL period fonts into tmp/ (not committed)
python3 tools/gen_period_data.py     # per-period sets -> docs/js/signs-<key>.js
```

## Fonts & credits

Period sign-forms are derived from cuneiform fonts by **S. Vanséveren** (Assurbanipal,
Santakku, SantakkuM, Ullikummi) and **C. Ziegeler** (Esagil), as used by eBL. The font files
are **not** committed (only the derived vector data); run `download_period_fonts.sh` to fetch
them. Confirm each font's terms before redistributing the fonts themselves.

## Layout

```
docs/
  index.html         the entire app (drawing + matcher + UI)
  js/signs-data.js   base set (Noto) + eBL MZL/readings (generated)
  js/signs-<key>.js  per-period vector sets: na, ob, mb, nb, hit (generated, lazy-loaded)
  fonts/             bundled Noto Sans Cuneiform (OFL)
tools/extract_signs.py       font -> vector data
tools/fetch_ebl_meta.py      eBL API -> MZL/ABZ/readings (cache: tools/ebl_meta.json)
tools/download_period_fonts.sh + gen_period_data.py   period fonts -> per-period data
model/             future embedding-model pipeline
cuneiform-sign-matcher-plan.md   original research + phased plan
```
