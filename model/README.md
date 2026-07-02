# Track B — the sign embedding model

Goal: a model that maps a **hand-drawn sketch** and a **reference sign** into the same
vector space, so the browser can do nearest-neighbour lookup by cosine similarity. This
replaces the placeholder shape-descriptor baseline in `../web/js/matcher.js` behind the
same `build()` / `query()` interface.

## What we reuse (and what we don't)

- **[`sign-embedding`](https://github.com/ElectronicBabylonianLiterature/sign-embedding)** — the
  right mechanism. Fine-tuned **ResNet-18**, final FC dropped → **512-dim** feature vectors;
  input 224×224 grayscale, ImageNet-normalized. **No pretrained checkpoint is published — it
  trains from scratch.** So we own a training step.
- **[`cuneiform-ocr-data`](https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data)**
  and the **2026 palaeography dataset**
  ([Zenodo 10.5281/zenodo.17949595](https://doi.org/10.5281/zenodo.17949595), from
  [this paper](https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.503)) — labeled
  sign crops (MZL / ABZ / sign name) for training. Downloaded from Zenodo, not in-repo.
- **NOT** `cuneiform-ocr/signs_match.ipynb` — despite the name it's DETR detection
  hyperparameter tuning, not sketch matching. Ignore for this purpose.

## The domain gap (the crux)

The datasets are sign *photos/line-drawings*. Users give *rough freehand sketches*. Plan to
close the gap:
1. Train the embedding on the sign-image data (reproduce `sign-embedding`).
2. Add **clean font-glyph renders** (Noto Sans Cuneiform, already bundled) as a second view
   of each sign — sketches resemble clean glyphs more than weathered tablets.
3. **Augment** heavily toward sketch-like inputs (elastic/stroke distortion, thinning,
   random affine, thresholding) and train contrastively (triplet / supervised-contrastive)
   so sketch and reference land near each other.

## Pipeline (to build)

```
1. fetch_data.py      download + unpack the Zenodo sign-image datasets  -> data/
2. render_glyphs.py   render every reference sign from the cuneiform font -> data/glyphs/
3. train.py           fine-tune ResNet-18 -> 512-d embedding (contrastive + augmentation)
4. export_onnx.py     export the trained backbone to model.onnx (opset for onnxruntime-web)
5. build_index.py     embed every reference sign -> web/data/sign_embeddings.json(.bin)
                      (codepoint / MZL / ABZ / glyph + 512-d vector)
```

The browser then loads `model.onnx` + the precomputed reference embeddings, runs the user's
normalized drawing through the model once, and cosine-ranks against the index — all offline.

## Environment

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # torch, torchvision, onnx, onnxruntime, pillow, numpy
```

## Open decisions (need the Assyriologists — see the plan)

- Reference sign standard: **MZL / ABZ / eBL internal**?
- Which **period(s)** first? (sign shape is period-dependent)
- Worth emailing the eBL / `sign-embedding` maintainers before training — they may share a
  checkpoint or want to collaborate.
