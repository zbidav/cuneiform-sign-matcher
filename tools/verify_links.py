import json, urllib.request, urllib.parse, concurrent.futures, os
HERE=os.path.dirname(os.path.abspath(__file__))+"/.."
d=json.loads(open(HERE+"/docs/js/signs-data.js").read()[len("window.SIGNS="):-2])
items=[(s["cp"], s["e"]) for s in d if s.get("e")]
def check(it):
    cp,e=it
    url="https://www.ebl.lmu.de/api/signs/"+urllib.parse.quote(e, safe="")
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"x"})
        with urllib.request.urlopen(req,timeout=15) as r:
            return cp,e,r.getcode()
    except urllib.error.HTTPError as ex: return cp,e,ex.code
    except Exception: return cp,e,0
dead=[]
alive=0
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    for cp,e,code in ex.map(check, items):
        if code==200: alive+=1
        else: dead.append((cp,e,code))
print(f"checked {len(items)} eBL links: alive={alive} dead={len(dead)}")
for cp,e,code in dead[:40]: print(f"  DEAD U+{cp} {e!r} -> {code}")
json.dump([cp for cp,e,code in dead], open(HERE+"/tools/dead_links.json","w"))
