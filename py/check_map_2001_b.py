# -*- coding: utf-8 -*-
"""20X20_01 vs 02: surface_terrain + 全物体清单 + hero→守卫 BFS 可达性"""
import zipfile, json
from collections import deque

def load(name):
    z = zipfile.ZipFile(f"/mnt/d/Bigdata/hero3_fresh/Maps/training/{name}")
    terr = json.loads(z.read("surface_terrain.json"))
    objs = json.loads(z.read("objects.json"))
    return terr, objs

for name in ["T03_adventure_20X20_01.vmap", "T03_adventure_20X20_02.vmap"]:
    terr, objs = load(name)
    print(f"\n=== {name} ===")
    print("terrain keys:", list(terr.keys())[:10] if isinstance(terr, dict) else type(terr))
    if isinstance(terr, dict):
        for k, v in terr.items():
            if isinstance(v, list) and v and isinstance(v[0], list):
                print(f"  {k}: {len(v)}x{len(v[0])} grid, sample row0: {v[0][:8]}")
            elif isinstance(v, list):
                print(f"  {k}: list[{len(v)}] sample: {v[:6]}")
            else:
                print(f"  {k}: {v}")
    print("objects:")
    for k, o in sorted(objs.items()):
        print(f"  {k}: type={o.get('type')} ({o.get('x')},{o.get('y')}) opts={str(o.get('options'))[:80]}")
