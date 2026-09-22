#!/usr/bin/env python3
"""#297 深挖 v2: King_of_Pain hero 样例 + 三图 random 对象全景 (09-22)"""
import json
import sys
import zipfile
from collections import Counter

sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")
from h3m2vmap import _loads_permissive as LJ


def load_objs(p):
    with zipfile.ZipFile(p) as z:
        return LJ(z.read("objects.json").decode("utf-8"))


print("===== REF King_of_Pain hero 样例")
objs = load_objs("/home/administrator/vcmi-native/rel/bin/data/Maps/King_of_Pain_h3m.vmap")
for o in objs:
    if isinstance(o, dict) and "hero" in str(o.get("type", "")).lower():
        print(json.dumps(o, ensure_ascii=False, indent=1)[:600])
        break

for tag, f in {
    "HANG_good_to_go": "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool/good_to_go_h3m.vmap",
    "HANG_judgement": "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool/judgement_day_h3m.vmap",
    "HANG_elbow": "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool/elbow_room_h3m.vmap",
}.items():
    print(f"\n===== {tag} random* / 特殊对象全景")
    objs = load_objs(f)
    rc = Counter(o.get("type") for o in objs if isinstance(o, dict)
                 and str(o.get("type", "")).startswith("random"))
    print("  random 类型:", dict(rc))
    # judgement 无 randomHero → 找它的英雄来源: predefinedHeroes/mainTown
    if "judgement" in tag:
        with zipfile.ZipFile(f) as z:
            h = LJ(z.read("header.json").decode("utf-8"))
        print("  players:", json.dumps(h.get("players"), ensure_ascii=False)[:300])
