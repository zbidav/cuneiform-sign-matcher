# Cuneiform Sign Matcher — Development Log

A running, detailed log of what the tool does and how each piece was built. Newest work at
the top. The app is a single static page (`docs/index.html`, no build step) plus generated
data files and the Python tools that produce them. Live: https://zbidav.github.io/cuneiform-sign-matcher/

---

## Feature summary (what the tool does now)

**Drawing & shape matching**
- Draw a sign several ways: **Line** (press–drag → one straight segment), **Freehand**
  (auto-straightened into segments via Ramer–Douglas–Peucker), **Box** (press–drag → a
  rectangle/frame), and **wedge stamps** — **Wedge** (real DIŠ glyph), **Short** (the same
  wedge compressed along its length), **Winkelhaken** (real U glyph) — click to place, **drag
  to set the angle**.
- **Select** tool: click a drawn line/box/wedge to select it (dashed box + a round handle),
  then **drag to move** it or **drag the handle to rotate** it about its centre.
- **Erase**: drag to **rub out the part** of a line/box under the cursor (the polyline is
  split); wedge stamps are removed whole. Scrub the whole stroke to clear it.
- Matching is geometric: the drawing and every reference sign are normalized to a unit box,
  densified into point clouds, and ranked by symmetric **chamfer distance**. One card per
  sign (best-matching form), ranked by similarity.
- **Read from a photo**: **📷 Photo** uploads (or, on a phone, takes) a picture of a tablet.
  It becomes a backdrop on the canvas — **Move/zoom** (drag to pan, mouse-wheel to zoom toward
  the cursor, ＋/－/Fit) — then **trace** the sign on top with Line / Freehand / wedges. The
  trace feeds the same matcher, so an unclear sign on the clay becomes a ranked candidate list.
  (The photo stays in the browser; nothing is uploaded anywhere.)
- **Image adjustments** (continuous, not presets): **brightness**, **contrast**, **grayscale**,
  and **dim** sliders, plus **invert** and a Sobel **edges** toggle (edges make wedge shadows
  pop on clay), and a **⟲ reset**. Applied live via `ctx.filter`.
- **Canvas size** control (small / medium / large / x-large) — the drawing canvas (and its
  column) grow on screen for detailed photo work; existing strokes + the photo scale to match,
  and the choice is remembered per browser.
- **Periods**: the reference set switches per period, generated from period-specific cuneiform
  fonts — Neo-Assyrian (Assurbanipal), Old Babylonian (Santakku), Middle Babylonian
  (SantakkuM), Neo-Babylonian (Esagil), Hittite (Ullikummi), Modern (Noto). **"All periods"**
  (default) matches across all ~2813 forms and tags each hit with the winning period.
  Candidates render in the selected period's script.
- **Show** selector (24/48/100/250/All) and a **Signs** filter (All / Basal only / Compound
  only; ~327 basal / ~552 compound).

**Sign reference (each candidate & the detail modal)**
- Cards show sign **name**, **readings**, **MZL number**, and shape-similarity score.
- Clicking a card opens a **detail modal**: enlarged glyph, full readings, **"Writes (words)"**
  (the Akkadian words the sign spells, each linked to its eBL dictionary entry, with English
  meanings), **"Combinations (writings it appears in)"** (multi-sign logograms like
  GAR.KUR = *šakin māti*, with links), and buttons **Add to canvas / Add to sentence /
  eBL sign page**.
- **Search box** matches by sign **name**, **reading**, OR **meaning** ("king" → LUGAL, BARA2).
- All eBL links verified: 752/879 signs deep-link to their eBL sign page (pipe-wrapped compound
  names); the rest go to the eBL search. Basal signs link to basal pages (not compounds).

**Sentence workspace (transcription surface)**
- Up to **10 lines**; click a line to make it active (new signs land there). Per-line delete,
  per-cell remove.
- **Type a line directly**: each line has an inline text field — type sign readings/names and
  **space** starts the next cell, **`...`** inserts a blank/gap. Known readings/names resolve to
  the actual sign glyph (`lugal kur` → LUGAL, KUR); anything unrecognised stays as an *italic
  text pill* you can **click to search** for the matching sign. Backspace on the empty field
  deletes the last cell. Typed tokens feed combination auto-detect and gap auto-complete too.
- **Reading disambiguation (homophony)**: a reading is often written by several signs
  (`gur` → EDIN / GUD / GUR / ZI₃). A typed cell shows a **▾N caret** with the count and,
  on click, a **chooser** listing every candidate sign (glyph + name + MZL + readings) to pick
  from — or **keep it as text** (a reading, not a sign), or search all. So "I typed GUR but
  meant a different sign" is one click to fix.
- **Reading variations via the dictionary (polyphony)**: a sign has many reading values
  (AB = ab / aš / eš₃ / …). For an all-signs line the gloss shows a **"could read:"** line —
  it enumerates each sign's *basic* reading values (homophone-index penalty ≤ 2, to cut
  coincidental noise), concatenates them across the line, and keeps only combinations that
  spell a **dictionary word** (`ba.bu` → *ba-bu* = **Babu**), each linked to its eBL entry.
  A conservative, honest suggestion — it only fires on confident basic-reading spellings.
- **Blank/gap cells** are editable text inputs — type a transliteration/note into a gap.
- **Drag to reorder** signs within/across lines, and **drag the ⠿ handle to reorder lines**.
- **Copy** exports the transcription (sign names + notes), line by line.
- **Confirm-before-clear** on both the canvas and the sentence.
- Persists in `localStorage`.
- **Combination auto-detect**: each line is matched against 1742 known logographic writings —
  a completed line shows its combination + Akkadian meaning (GAR.KUR = *šakin māti*).
- **Gap auto-complete**: a line with a blank suggests which signs complete a real writing
  (KA.▢ → DU₁₁.DU₁₁ *dabābu*, gap: du11), and the suggestion is **clickable to fill the blank**.

**UI**
- **Dark mode** toggle (black screen, white signs; canvas themed in JS; remembered per browser).

---

## Data & tools (`tools/`, all offline-reproducible)

- `extract_signs.py` — renders every Unicode cuneiform sign (U+12000–U+1236E) from a font,
  flattens outlines to line segments, RDP-decimates → `docs/js/signs-data.js`
  (`window.SIGNS` = `{c, cp, n(name), g(contours)}` per sign). Also the per-period sets.
- `download_period_fonts.sh` + `gen_period_data.py` — fetch eBL's period fonts (S. Vanséveren:
  Assurbanipal/Santakku/SantakkuM/Ullikummi; C. Ziegeler: Esagil) and generate per-period
  vector sets `docs/js/signs-{na,ob,mb,nb,hit}.js`. Fonts are CC BY 4.0; NOT committed (only
  the derived data), credited in the footer.
- `fetch_ebl_meta.py` — enriches signs from the eBL public API: **MZL/ABZ** sign-list numbers,
  **readings** (with homophone index, value+subIndex → "gur2"), **logogram words** (`lg`), and
  **combinations** (`cb` = [form, Akkadian reading]). Two-pass: MZL-number sweep (maps by the
  sign's `unicode` codepoint; prefers the least-compound name so basal signs stay basal) +
  name-based fallback. Cached to `tools/ebl_meta.json`.
- `fetch_words.py` — pulls the English guide-word (meaning) for every logogram lemma from the
  eBL dictionary → `docs/js/words-data.js` (`window.WORDS`, 1888 lemma→meaning).
- `benchmark_recall.py` — measures top-k retrieval recall (perturb a sign, see if it returns).
- `verify_links.py` — checks every eBL link resolves (all 752 verified alive).

**Key eBL public API endpoints used**: `/api/signs/<NAME>` (readings, logograms, lists,
unicode), `/api/signs?listsName=MZL&listsNumber=N` (bulk), `/api/words?query=` and
`/api/words/<id>` (dictionary), site pages `/tools/signs/<NAME>` and `/dictionary/<id>`.
The **corpus/fragment text is gated** (login), so statistical sign co-occurrence n-grams
aren't yet possible without corpus access.

---

## Deployment

Hosted on **GitHub Pages, Deploy-from-a-branch** — Settings → Pages → Source = "Deploy from a
branch", branch `main`, folder **`/docs`** (`docs/.nojekyll` bypasses Jekyll). Changing the
source/folder does **not** auto-rebuild — push a commit (empty is fine) to trigger a build.

**Why not Actions:** the earlier `.github/workflows/deploy-pages.yml` (kept as
`workflow_dispatch`-only) relied on `actions/deploy-pages@v4`, whose "Deploy to Pages" step wedged
on GitHub's Pages backend (Node 20→24 rollout). Branch-deploy uses the separate legacy "pages build
and deployment" path, which does not wedge. Folder must be `/docs`, not `/ (root)` — with root,
Jekyll themes the top-level README instead of serving the app.

**The Pages outage (resolved):** mid-session, Pages stopped publishing. Diagnosis via the
public Actions API showed the Jekyll build then the `actions/deploy-pages` step failing
(`getPagesDeploymentStatus: Not Found`, later a wedged deployment holding the lock — a symptom
of GitHub's Node 20→24 Pages rollout). `.nojekyll`, source toggles, and a full Pages
disable/re-enable did **not** clear it. **The fix that worked:** *delete the `github-pages`
environment* (Settings → Environments → github-pages → Delete), then re-enable Pages as
GitHub Actions and deploy once — a fresh environment with no stuck deployment. The several
"retry/trigger deploy" commits in history are artifacts of that fight.

---

## Roadmap / open threads

- **Corpus n-grams** (statistical which-sign-follows-which) — needs eBL's gated corpus or an
  ORACC/CDLI ATF proxy.
- **Old-Assyrian sign forms** — no Unicode font exists; would require deriving vectors from the
  palaeography image dataset (a CV task).
- **ML embedding model** (`model/`) — the accuracy upgrade for messy sketches (eBL's
  `sign-embedding`, ResNet-18 → ONNX in-browser); needs training (no published checkpoint).
- Rank meaning-search hits by which sign is a word's *primary* logogram.
