#!/usr/bin/env python3
"""Extract vector outlines for every Unicode cuneiform sign from the bundled font
and emit a compact JS data file (window.SIGNS). Curves are flattened to straight
segments and each contour is decimated (Ramer-Douglas-Peucker), so signs become
line/vector data suitable for geometric matching against hand-drawn strokes."""

import json
import unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

import os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(HERE, "docs/fonts/NotoSansCuneiform-Regular.ttf")
OUT  = os.path.join(HERE, "docs/js/signs-data.js")
CP_LO, CP_HI = 0x12000, 0x1236E


def q(p0, p1, p2, n):
    return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0],
             (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in [i/n for i in range(1, n+1)]]

def c(p0, p1, p2, p3, n):
    return [((1-t)**3*p0[0]+3*(1-t)**2*t*p1[0]+3*(1-t)*t*t*p2[0]+t**3*p3[0],
             (1-t)**3*p0[1]+3*(1-t)**2*t*p1[1]+3*(1-t)*t*t*p2[1]+t**3*p3[1]) for t in [i/n for i in range(1, n+1)]]


class Flatten(BasePen):
    def __init__(self, gs, steps=6):
        super().__init__(gs); self.contours = []; self.cur = None; self.steps = steps
    def _moveTo(self, pt): self.cur = [pt]; self.contours.append(self.cur)
    def _lineTo(self, pt): self.cur.append(pt)
    def _qCurveToOne(self, p1, p2): self.cur += q(self.cur[-1], p1, p2, self.steps)
    def _curveToOne(self, p1, p2, p3): self.cur += c(self.cur[-1], p1, p2, p3, self.steps)
    def _closePath(self): pass   # keep contour open; renderer closes it
    def _endPath(self): pass


def rdp(pts, eps):
    if len(pts) < 3: return pts
    x1, y1 = pts[0]; x2, y2 = pts[-1]
    dx, dy = x2-x1, y2-y1; L = (dx*dx+dy*dy) ** 0.5
    dmax, idx = 0, 0
    for i in range(1, len(pts)-1):
        x0, y0 = pts[i]
        if L < 1e-6:                          # closed/degenerate span: use radial distance
            d = ((x0-x1)**2 + (y0-y1)**2) ** 0.5
        else:
            d = abs(dy*x0 - dx*y0 + x2*y1 - y2*x1) / L
        if d > dmax: dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx+1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def main():
    f = TTFont(FONT)
    em = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    eps = em * 0.012
    signs = []
    for cp in range(CP_LO, CP_HI+1):
        if cp not in cmap: continue
        pen = Flatten(gs)
        try:
            gs[cmap[cp]].draw(pen)
        except Exception:
            continue
        contours = []
        for ct in pen.contours:
            if len(ct) < 2: continue
            d = rdp(ct, eps)
            contours.append([[round(x), round(y)] for x, y in d])
        if not contours: continue
        # Sign name from the Unicode character name (e.g. "CUNEIFORM SIGN GU" -> "GU").
        # These names largely match eBL's sign-list names, so they double as eBL deep-links.
        try:
            nm = unicodedata.name(chr(cp))
        except ValueError:
            nm = ""
        for pre in ("CUNEIFORM SIGN ", "CUNEIFORM NUMERIC SIGN ", "CUNEIFORM PUNCTUATION SIGN "):
            if nm.startswith(pre):
                nm = nm[len(pre):]
                break
        signs.append({"c": chr(cp), "cp": format(cp, "X"), "n": nm, "g": contours})
    payload = "window.SIGNS=" + json.dumps(signs, separators=(",", ":")) + ";\n"
    with open(OUT, "w") as fh:
        fh.write(payload)
    npts = sum(len(ct) for s in signs for ct in s["g"])
    print(f"signs={len(signs)} points={npts} bytes={len(payload)} em={em}")


if __name__ == "__main__":
    main()
