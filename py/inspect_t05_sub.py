import zipfile, json, glob
from collections import Counter
all_sub = Counter()
for p in sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_*.vmap')):
    z = zipfile.ZipFile(p)
    o = json.loads(z.read("objects.json"))
    subs = [(k, v["subtype"], v["options"].get("amount")) for k, v in o.items() if v["type"] == "monster"]
    heros = [(k, v["options"]["army"][3]) for k, v in o.items() if v["type"] == "hero"]
    towns = [(k, v["subtype"]) for k, v in o.items() if v["type"] == "town"]
    print(p.split('/')[-1])
    for s in subs: print("  ", s)
    for h in heros: print("  hero:", h)
    print("  towns:", towns)
    for _, st, _a in subs: all_sub[st] += 1
print("=== 全部 monster subtype:", dict(all_sub))
