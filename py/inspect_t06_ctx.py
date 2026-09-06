#!/usr/bin/env python3
"""T06 前置补充检验: town owner / 英雄数 / 与 T05 结构对比"""
import zipfile, json, glob

for p in sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_adventure_36X36_01.vmap')
                + glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T06_adventure_*.vmap')):
    z = zipfile.ZipFile(p)
    o = json.loads(z.read("objects.json"))
    towns = [(k, v.get("subtype"), v["options"].get("owner"), (v["x"], v["y"]))
             for k, v in o.items() if v["type"] == "town"]
    heroes = [(k, v["options"].get("owner")) for k, v in o.items() if v["type"] == "hero"]
    mines = [(k, v.get("subtype"), v["options"].get("owner")) for k, v in o.items() if v["type"] == "mine"]
    win = None
    try:
        hdr = json.loads(z.read("header.json"))
        win = hdr.get("victoryCondition") or hdr.get("victory")
    except Exception:
        pass
    print(f"=== {p.split('/')[-1]}")
    print(f"  towns: {towns}")
    print(f"  heroes: {heroes}")
    print(f"  mines: {mines}")
    print(f"  victory: {win}")
