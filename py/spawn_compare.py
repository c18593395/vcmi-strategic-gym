#!/usr/bin/env python3
"""T05 vs T06 英雄出生位置对照 (T05=城上出生, RECRUITED 历史验证过的约定)"""
import json
import zipfile

for base in ["T05_adventure_36X36_01", "T06_adventure_108X108_02_duel"]:
    z = zipfile.ZipFile(f"/mnt/d/Bigdata/hero3_fresh/maps/training/{base}.vmap")
    objs = json.loads(z.read('objects.json').decode('utf-8', 'ignore'))
    print("==", base)
    for k, o in objs.items():
        t = str(o.get("type", ""))
        if "hero" in t or "town" in t:
            print(f"   {k} {t} pos=({o.get('x')},{o.get('y')}) owner={o.get('options', {}).get('owner')}")
