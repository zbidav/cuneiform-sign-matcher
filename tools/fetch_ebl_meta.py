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


def ebl_name(n):
    # Unicode sign name -> eBL sign-list name (e.g. "KA TIMES BAD" -> "KA×BAD").
    return n.replace(" TIMES ", "×").replace(" PLUS ", "+")


def load_signs():
    txt = open(DATA).read()
    return json.loads(txt[len("window.SIGNS="):-2])


def fetch_one(sign):
    cp, nm = sign["cp"], sign.get("n", "")
    if not nm:
        return cp, None
    url = API + urllib.parse.quote(ebl_name(nm), safe="")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cuneiform-matcher/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            d = json.load(r)
    except Exception:
        return cp, None
    lists = {l.get("name"): l.get("number") for l in d.get("lists", [])}
    readings = [v.get("value") for v in d.get("values", []) if v.get("value")]
    return cp, {"mzl": lists.get("MZL"), "abz": lists.get("ABZ"), "readings": readings}


def main():
    signs = load_signs()
    refresh = "--refresh" in sys.argv
    if os.path.exists(CACHE) and not refresh:
        meta = json.load(open(CACHE))
        print(f"loaded {len(meta)} cached eBL records (use --refresh to re-fetch)")
    else:
        meta = {}
        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            for cp, m in ex.map(fetch_one, signs):
                done += 1
                if m and (m.get("mzl") or m.get("readings")):
                    meta[cp] = m
                if done % 100 == 0:
                    print(f"  fetched {done}/{len(signs)} (hits so far: {len(meta)})", flush=True)
        json.dump(meta, open(CACHE, "w"))
        print(f"fetched; {len(meta)} signs matched an eBL entry -> cached")

    for s in signs:
        m = meta.get(s["cp"])
        if not m:
            continue
        if m.get("mzl"):
            s["m"] = m["mzl"]
        if m.get("abz"):
            s["z"] = m["abz"]
        if m.get("readings"):
            s["r"] = m["readings"][:6]
    payload = "window.SIGNS=" + json.dumps(signs, separators=(",", ":")) + ";\n"
    open(DATA, "w").write(payload)
    enriched = sum(1 for s in signs if "m" in s or "r" in s)
    print(f"merged: {enriched}/{len(signs)} signs now carry MZL/readings; bytes={len(payload)}")


if __name__ == "__main__":
    main()
