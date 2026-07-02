#!/usr/bin/env python3
"""Fetch the English guide-word (meaning) for every logogram lemma referenced by the signs,
so the app can (a) show meanings next to the words a sign writes and (b) let users find a
sign by meaning ("king" -> šarru -> LUGAL) fully offline.

Source: eBL dictionary API /api/words/<lemmaId>. Output: docs/js/words-data.js
(window.WORDS = {lemmaId: guideWord}). Cached to tools/words_meta.json; --refresh to re-fetch.
Run after tools/fetch_ebl_meta.py (which populates each sign's `lg` logogram lemmas).
"""

import json, os, sys, urllib.request, urllib.parse, concurrent.futures

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "docs/js/signs-data.js")
OUT = os.path.join(HERE, "docs/js/words-data.js")
CACHE = os.path.join(HERE, "tools/words_meta.json")
API = "https://www.ebl.lmu.de/api/words/"


def lemmas_from_signs():
    signs = json.loads(open(DATA).read()[len("window.SIGNS="):-2])
    lem = set()
    for s in signs:
        for w in s.get("lg", []) or []:
            lem.add(w)
    return sorted(lem)


def fetch(wid):
    url = API + urllib.parse.quote(wid, safe="")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cuneiform-matcher/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            d = json.load(r)
    except Exception:
        return wid, None
    return wid, (d.get("guideWord") or "").strip()


def main():
    refresh = "--refresh" in sys.argv
    if os.path.exists(CACHE) and not refresh:
        words = json.load(open(CACHE))
        print(f"loaded {len(words)} cached word meanings (use --refresh to re-fetch)")
    else:
        lemmas = lemmas_from_signs()
        words = {}
        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            for wid, gw in ex.map(fetch, lemmas):
                done += 1
                if gw:
                    words[wid] = gw
                if done % 300 == 0:
                    print(f"  fetched {done}/{len(lemmas)} (meanings so far: {len(words)})", flush=True)
        json.dump(words, open(CACHE, "w"))
        print(f"fetched meanings for {len(words)}/{len(lemmas)} lemmas -> cached")

    payload = "window.WORDS=" + json.dumps(words, separators=(",", ":"), ensure_ascii=False) + ";\n"
    open(OUT, "w").write(payload)
    print(f"wrote {OUT} ({len(payload)} bytes)")


if __name__ == "__main__":
    main()
