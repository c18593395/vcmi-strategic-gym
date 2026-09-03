import zipfile, json, glob
for p in sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_*.vmap')):
    z = zipfile.ZipFile(p)
    o = json.loads(z.read("objects.json"))
    hdr = json.loads(z.read("header.json"))
    from collections import Counter
    types = Counter(v["type"] for v in o.values())
    heroes = {k: (v["x"], v["y"], v["options"].get("owner"), v["options"].get("army", [{}]*7)[3]) for k, v in o.items() if v["type"] == "hero"}
    guards = {k: (v["x"], v["y"], v.get("options", {}).get("amount")) for k, v in o.items() if "monster" in v["type"]}
    print(p.split('/')[-1], dict(types))
    print("  heroes:", heroes)
    print("  guards:", dict(list(guards.items())[:4]))
