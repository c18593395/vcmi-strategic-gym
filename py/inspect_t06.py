import zipfile, json, glob
from collections import Counter

# T04 已验证校准集 (合法 identifier)
VALID_CREATURES = {'core:peasant', 'core:archer', 'core:swordsman'}
VALID_TOWN = {'core:dungeon', 'core:conflux'}
VALID_RES = {'core:gold', 'core:wood', 'core:crystal'}
VALID_MINE = {'core:goldMine'}
VALID_HERO = {'core:edric', 'core:iona', 'core:alchemist'}

for p in sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T06_*.vmap')):
    z = zipfile.ZipFile(p)
    o = json.loads(z.read("objects.json"))
    t = json.loads(z.read("surface_terrain.json"))
    hdr = json.loads(z.read("header.json"))
    h, w = len(t), len(t[0])
    types = Counter(v["type"] for v in o.values())
    print(f"=== {p.split('/')[-1]}  {w}x{h}")
    print(f"  对象: {dict(types)}")
    issues = []
    for k, v in o.items():
        st = v.get("subtype", "")
        if v["type"] == "monster" and st not in VALID_CREATURES:
            issues.append(f"{k} monster {st} x{v['options'].get('amount')}")
        if v["type"] == "hero" and (v["options"].get("type") not in VALID_HERO or v["options"].get("portrait") not in VALID_HERO):
            issues.append(f"{k} hero {v['options'].get('type')}/{v['options'].get('portrait')}")
        if v["type"] == "resource" and st not in VALID_RES:
            issues.append(f"{k} resource {st}")
        if v["type"] == "town" and st not in VALID_TOWN:
            issues.append(f"{k} town {st}")
        if v["type"] == "mine" and st not in VALID_MINE:
            issues.append(f"{k} mine {st}")
    print(f"  非法 identifier: {issues if issues else '无 ✓'}")
    for k, v in o.items():
        if v["type"] in ("hero", "monster"):
            amt = v["options"].get("army", [{}]*7)[3] if v["type"] == "hero" else v["options"].get("amount")
            print(f"  {k}: {v['type']} ({v['x']},{v['y']}) owner={v['options'].get('owner')} 兵={amt}")
