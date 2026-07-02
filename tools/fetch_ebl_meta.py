#!/usr/bin/env python3
"""Enrich docs/js/signs-data.js with authoritative metadata from the eBL public API
(https://www.ebl.lmu.de/api/signs/<NAME>): MZL & ABZ sign-list numbers and readings.

Runs offline-reproducibly: results are cached to tools/ebl_meta.json (committed), so a
re-run merges from cache without re-hitting eBL. Pass --refresh to re-fetch from the API.

Pipeline order: tools/extract_signs.py (base vector data) -> tools/fetch_ebl_meta.py (enrich).
"""

import json, os, sys, urllib.request, urllib.parse, concurrent.futures

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "docs/js/signs-data.js")
CACHE = os.path.join(HERE, "tools/ebl_meta.json")
API = "https://www.ebl.lmu.de/api/signs/"


SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def ebl_name(n):
    # Unicode sign name -> eBL sign-list name (e.g. "KA TIMES BAD" -> "KA×BAD").
    return n.replace(" TIMES ", "×").replace(" PLUS ", "+")


def candidates(nm):
    # eBL wraps COMPOUND signs in pipes (|KA×BAD|) and uses subscript digits (GAN₂).
    # Yield the most likely forms first; the first that returns 200 wins.
    base = ebl_name(nm)
    if any(c in base for c in "×+&.· "):
        yield "|%s|" % base
        subbed = "|%s|" % base.translate(SUB)
        if subbed != "|%s|" % base:
            yield subbed
        yield base
    else:
        yield base


def load_signs():
    txt = open(DATA).read()
    return json.loads(txt[len("window.SIGNS="):-2])


def fetch_one(sign):
    cp, nm = sign["cp"], sign.get("n", "")
    if not nm:
        return cp, None
    for cand in candidates(nm):
        url = API + urllib.parse.quote(cand, safe="")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "cuneiform-matcher/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                d = json.load(r)
        except Exception:
            continue
        lists = {l.get("name"): l.get("number") for l in d.get("lists", [])}
        readings = [v.get("value") for v in d.get("values", []) if v.get("value")]
        # `ebl` is the exact name string that resolved -> use it to build the sign-page link.
        return cp, {"ebl": cand, "mzl": lists.get("MZL"), "abz": lists.get("ABZ"), "readings": readings}
    return cp, None


def fetch_mzl(n):
    # Query eBL by MZL number and map results back to Unicode codepoints via each sign's
    # `unicode` field. Far more reliable than guessing name spellings: it uses eBL's own
    # canonical name (usable directly in the sign-page URL) and codepoint.
    url = "https://www.ebl.lmu.de/api/signs?listsName=MZL&listsNumber=%d" % n
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cuneiform-matcher/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.load(r)
    except Exception:
        return []
    recs = []
    for d in data if isinstance(data, list) else []:
        lists = {l.get("name"): l.get("number") for l in d.get("lists", [])}
        readings = [v.get("value") for v in d.get("values", []) if v.get("value")]
        rec = {"ebl": d.get("name"), "mzl": lists.get("MZL"), "abz": lists.get("ABZ"), "readings": readings}
        for cp in d.get("unicode", []):
            recs.append((format(int(cp), "X"), rec))
    return recs


def main():
    signs = load_signs()
    refresh = "--refresh" in sys.argv
    if os.path.exists(CACHE) and not refresh:
        meta = json.load(open(CACHE))
        print(f"loaded {len(meta)} cached eBL records (use --refresh to re-fetch)")
    else:
        meta = {}
        # Pass 1: sweep MZL numbers, map to codepoints (authoritative, high coverage).
        MAXMZL = 1000
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            done = 0
            for recs in ex.map(fetch_mzl, range(1, MAXMZL + 1)):
                done += 1
                for cp, rec in recs:
                    meta.setdefault(cp, rec)
                if done % 200 == 0:
                    print(f"  MZL sweep {done}/{MAXMZL} (codepoints so far: {len(meta)})", flush=True)
        print(f"MZL sweep done: {len(meta)} codepoints mapped")
        # Pass 2: name-based fallback only for signs still missing.
        missing = [s for s in signs if s["cp"] not in meta]
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            for cp, m in ex.map(fetch_one, missing):
                if m:
                    meta.setdefault(cp, m)
        json.dump(meta, open(CACHE, "w"))
        print(f"fetched; {len(meta)} codepoints have eBL data -> cached")

    for s in signs:
        m = meta.get(s["cp"])
        if not m:
            continue
        if m.get("ebl"):
            s["e"] = m["ebl"]
        if m.get("mzl"):
            s["m"] = m["mzl"]
        if m.get("abz"):
            s["z"] = m["abz"]
        if m.get("readings"):
            s["r"] = m["readings"][:6]
    payload = "window.SIGNS=" + json.dumps(signs, separators=(",", ":")) + ";\n"
    open(DATA, "w").write(payload)
    enriched = sum(1 for s in signs if "e" in s)
    print(f"merged: {enriched}/{len(signs)} signs now carry MZL/readings; bytes={len(payload)}")


if __name__ == "__main__":
    main()
