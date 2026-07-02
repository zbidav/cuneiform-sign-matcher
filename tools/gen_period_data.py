#!/usr/bin/env python3
"""Generate per-period vector sign data by running the outline extractor over each of
eBL's period-specific cuneiform fonts. Each font renders the SAME Unicode codepoints in a
period style, so one reference set per font gives real period-aware matching.

Fonts (downloaded to tmp/periodfonts/ by tools/download_period_fonts.sh; NOT committed):
  Assurbanipal  Neo-Assyrian    (S. Vanseveren)   full 879
  Esagil        Neo-Babylonian  (C. Ziegeler)     full 879
  Santakku      Old Babylonian  (S. Vanseveren)   297
  SantakkuM     Middle Babylonian (S. Vanseveren) 222
  UllikummiA    Hittite         (S. Vanseveren)   322

Output: docs/js/signs-<key>.js -> window.SIGNS_<VAR> = [{c,cp,n,g}], geometry + name only.
MZL/ABZ/readings are period-independent and joined at runtime from the base signs-data.js.
"""

import json, os, unicodedata
from fontTools.ttLib import TTFont
from extract_signs import Flatten, rdp, CP_LO, CP_HI

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FDIR = os.path.join(HERE, "tmp/periodfonts")

# key -> (font file, JS variable suffix)
FONTS = {
    "na":  ("Assurbanipal.ttf", "NA"),
    "ob":  ("Santakku.woff",    "OB"),
    "mb":  ("SantakkuM.woff",   "MB"),
    "nb":  ("Esagil.woff",      "NB"),
    "hit": ("UllikummiA.woff",  "HIT"),
}


def sign_name(cp):
    try:
        nm = unicodedata.name(chr(cp))
    except ValueError:
        return ""
    for pre in ("CUNEIFORM SIGN ", "CUNEIFORM NUMERIC SIGN ", "CUNEIFORM PUNCTUATION SIGN "):
        if nm.startswith(pre):
            return nm[len(pre):]
    return nm


def build(font_path, var):
    f = TTFont(font_path)
    em = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    eps = em * 0.012
    signs = []
    for cp in range(CP_LO, CP_HI + 1):
        if cp not in cmap:
            continue
        pen = Flatten(gs)
        try:
            gs[cmap[cp]].draw(pen)
        except Exception:
            continue
        contours = []
        for ct in pen.contours:
            if len(ct) < 2:
                continue
            d = rdp(ct, eps)
            contours.append([[round(x), round(y)] for x, y in d])
        if not contours:
            continue
        signs.append({"c": chr(cp), "cp": format(cp, "X"), "n": sign_name(cp), "g": contours})
    payload = "window.SIGNS_%s=%s;\n" % (var, json.dumps(signs, separators=(",", ":")))
    out = os.path.join(HERE, "docs/js/signs-%s.js" % var.lower())
    open(out, "w").write(payload)
    return len(signs), len(payload), out


def main():
    for key, (fname, var) in FONTS.items():
        fp = os.path.join(FDIR, fname)
        if not os.path.exists(fp):
            print(f"  SKIP {key}: missing {fp}")
            continue
        n, b, out = build(fp, var)
        print(f"  {key:4s} {fname:16s} -> {os.path.basename(out):16s} signs={n:4d} bytes={b}")


if __name__ == "__main__":
    main()
