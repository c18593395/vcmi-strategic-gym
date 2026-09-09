#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0910 T05 36X36_02 重设计分析: 对象布局 + 地形障碍 dump, 对照 36X36_01"""
import zipfile, json, sys

MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/maps/training/"
NAMES = ["T05_adventure_36X36_01.vmap", "T05_adventure_36X36_02.vmap"]

for name in NAMES:
    z = zipfile.ZipFile(MAP_DIR + name)
    objs = json.loads(z.read("objects.json"))
    print("=====", name)
    try:
        terr = json.loads(z.read("surface_terrain.json"))
        print("  terrain entries:", len(terr), "sample:", json.dumps(dict(list(terr.items())[:2]))[:200])
    except Exception as e:
        print("  surface_terrain: NA", e)
    # 地形障碍统计 (rc00_ 岩石 / wa 水体)
    try:
        terr = json.loads(z.read("surface_terrain.json"))
        rock, water = [], []
        for pos, code in terr.items():
            c = str(code)
            if c.startswith("rc"): rock.append(pos)
            elif c.startswith("wa"): water.append(pos)
        print(f"  rocks(rc*): {len(rock)}  water(wa*): {len(water)}")
        if rock: print("   rock positions:", sorted(rock)[:40])
    except Exception:
        pass
    for k, o in sorted(objs.items()):
        opt = o.get("options", {})
        print("  %-14s (%s,%s) type=%s sub=%s owner=%s amount=%s" % (
            k, o.get("x"), o.get("y"), o.get("type"), o.get("subtype", ""),
            opt.get("owner", ""), opt.get("amount", "")))
