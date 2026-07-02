# Cuneiform Sign-Matching Tool — Project Summary

**Status:** Planning stage, no code written yet.
**Goal:** A tool that lets Assyriologists draw an unknown cuneiform sign and get back a ranked list of likely matches from the eBL sign list, so they don't have to flip through paper sign-lists or fight a slow connection to search eBL by name/transliteration.

---

## 1. Background: relevant cuneiform text resources

| Resource | URL | What it is |
|---|---|---|
| **eBL** (electronic Babylonian Library) — the main target | https://www.ebl.lmu.de/ | Platform for editing/reconstructing Babylonian literary texts from cuneiform tablets. Based at LMU Munich + Bavarian Academy of Sciences. Has a searchable sign list, a "Fragmentarium," and (see below) an actual AI pipeline behind the scenes. |
| eBL sign search | https://www.ebl.lmu.de/signs | The sign-list lookup the Assyriologists currently struggle with (text/font-based search only, no draw-to-search). |
| CDLI (Cuneiform Digital Library Initiative) | https://cdli.mpiwg-berlin.mpg.de/ | Broader raw-tablet database (admin/economic texts too, not just literature), with photos + metadata. |
| ORACC | http://oracc.org/ | Another major hub, many sub-projects, often includes English translations. |

eBL is the right primary target since that's what the Assyriologists already use and struggle with.

---

## 2. The core problem

Assyriologists want to identify an unfamiliar cuneiform sign. Today: paper sign-lists, or a slow/unreliable text search on eBL. They want to **draw the sign** and get candidate matches back.

This is conceptually a **sketch-based image retrieval (SBIR)** problem — same family of problem as Google's "Quick, Draw!" — not classic OCR, because the input is a rough hand-drawn approximation, not a photo of an actual tablet.

---

## 3. Key finding: eBL already built most of the needed infrastructure

This is the most important discovery from our research — **we should extend/reuse eBL's existing tools rather than starting from zero.** All under the `ElectronicBabylonianLiterature` GitHub org:

| Repo | Relevance |
|---|---|
| [`ebl-api`](https://github.com/ElectronicBabylonianLiterature/ebl-api) | The production API. Has a public sign-list endpoint and fragment/transliteration data. This is likely how a prototype would fetch canonical sign data (names, MZL/Borger/ABZ sign-list numbers, font glyphs). |
| [`cuneiform-ocr`](https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr) | Trained deep learning model (FCENet + ResNet-18 backbone) that detects & classifies cuneiform signs on tablet photos. Run across ~75,000 tablet photos, extracted 1.2M+ sign instances. **Contains a notebook called `signs_match.ipynb`** — worth reading first, it may already do something very close to what we want. |
| [`ebl-ai-api`](https://github.com/ElectronicBabylonianLiterature/ebl-ai-api) | Server that deploys the above model for inference. Good reference for how to structure an inference server. |
| [`sign-embedding`](https://github.com/ElectronicBabylonianLiterature/sign-embedding) | Repo name strongly suggests embedding-space representation of signs — exactly the mechanism we'd want for similarity search. **We have not yet inspected its actual contents/README** — this should be the very first thing to check when work resumes. |
| [`cuneiform-ocr-data`](https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data) | Labeled sign image data tied to sign-list numbers, aggregated from multiple digitized sign catalogues (CDP, Labasi, etc.). Candidate training/reference data. |
| [`ngram-matcher`](https://github.com/ElectronicBabylonianLiterature/ngram-matcher) | Different problem (matches overlapping text fragments), but shows the team's general approach to fuzzy matching in this domain. |

**Also relevant:**
- Published paper: *"Sign Detection for Cuneiform Tablets"* — Cobanoglu, Sáenz, Khait, Jiménez, 2024. DOI: [10.1515/itit-2024-0028](https://doi.org/10.1515/itit-2024-0028)
- New (2026) dataset paper: *"A Large-Scale Dataset of Annotated Cuneiform Sign Images for Digital Palaeography"* — https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.503 (data DOI: 10.5281/zenodo.17949595). Purpose-built for training sign classifiers — strong candidate reference/training set.

**Action item:** it's worth opening a GitHub issue / contacting the eBL team directly before building much — they may already have an embedding checkpoint, may be interested in collaborating, or may tell us "we tried this, here's why it's hard."

---

## 4. Proposed technical approach

**Match against simplified reference glyphs, not raw tablet photos.** A hand sketch is visually much closer to a clean font-rendered sign shape than to a photo of a broken, weathered clay tablet. eBL's own sign pages already use rendered fonts for each sign — a good candidate reference set.

**Use a learned embedding space, not raw pixel comparison.** Train (or reuse) a model that maps both sketches and reference glyphs into the same vector space (contrastive/triplet-loss style), then do nearest-neighbor lookup via cosine similarity. This tolerates messy, imprecise drawing far better than pixel-diffing.

**Return a ranked top-k list, not a single answer.** Many signs are visually close (especially period-to-period variants), so the honest and more useful product is "here are your 10 best candidates with links to their eBL sign pages," not a single guess.

**Sign shape is period-dependent.** The same sign can look quite different in Old Babylonian vs. Neo-Assyrian, for instance. This needs to be scoped explicitly with the Assyriologists (see open questions).

---

## 5. Phased plan

- **Phase 0 — Scope with the Assyriologists.** Which period(s)/sign list matters most? Do they want a single best guess or a ranked list? What metadata should come back (MZL number, transliteration value, link to eBL page)?
- **Phase 1 — Reuse, don't rebuild.** Contact eBL/`sign-embedding` maintainers; pull labeled sign images from `cuneiform-ocr-data` and/or the 2026 palaeography dataset as the reference set.
- **Phase 2 — Thin prototype.** HTML5 `<canvas>` drawing pad → normalize the drawing the same way training images are normalized → run through the embedding model → cosine similarity against reference embeddings → return top-k with images + sign numbers + eBL links.
- **Phase 3 — Test with real users.** Have the Assyriologists try it on signs they remember struggling with; see where it breaks (likely: visually similar sign families, period-specific variants).
- **Phase 4 (stretch) — Structural/wedge-based matching.** Cuneiform signs are literally built from wedges. A symbolic representation (wedge count, orientation, relative position) as a complementary signal to the embedding approach, closer to how a person actually thinks while sketching.

---

## 6. Tech stack notes

Given the user's background (R, Unix shell, some Python):

- The ML/embedding piece is realistically **Python** territory (PyTorch/mmdetection-adjacent ecosystem — eBL's own repos use PyTorch, mmocr, mmpretrain). No good way around this for the CV model itself.
- **Shell scripting** fits naturally for data pipeline glue: downloading/preparing datasets, running training or inference jobs, deployment scripting.
- **R** is less central here since this is a CV/deep-learning task, but could be useful downstream — e.g., analyzing retrieval accuracy / usage logs once the tool is being tested by the Assyriologists.
- When continuing in Claude Code: expect most new code to be Python, with inline comments explaining what each part does (per usual preference), and shell scripts for orchestration where that's more natural.

---

## 7. Open questions to resolve before/early in Claude Code

1. Which sign list is the reference standard — Borger's MZL, ABZ, or eBL's own internal list? (They're cross-referenced but not identical.)
2. Which period(s) of cuneiform should the tool prioritize first?
3. Has anyone already reached out to the eBL/`sign-embedding` team? Worth doing before duplicating effort.
4. What does `sign-embedding`'s README actually say it does? (Unread as of this summary — check first.)
5. What does `cuneiform-ocr/signs_match.ipynb` actually contain? (Also unread — check first, may shortcut a lot of this plan.)
6. Deployment target: is this meant to run on the user's own server (offline-capable, addressing the "internet doesn't work" pain point), or as a hosted web tool?

---

## 8. Conversation history note

This summary reflects a single planning conversation (no prior conversations found in this project, no uploaded data files). Two research passes were done via web search: one to identify eBL itself, and one to map out eBL's existing GitHub infrastructure and prior published work.
