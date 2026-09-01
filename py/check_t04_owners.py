#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查 T04 objects.json 的 owner 分布 (town/hero 归属) → 推断 standardDefeat 胜利路径"""
import json, zipfile, glob, os

for p in sorted(glob.glob("/mnt/d/Bigdata/hero3_fresh/maps/training/T04_adventure_*.vmap"))[:2]:
    name = os.path.basename(p)
    print(f"===== {name}")
    with zipfile.ZipFile(p) as z:
        objs = json.loads(z.read("objects.json"))
        hdr = json.loads(z.read("header.json"))
    # 玩家配置
    for k in hdr:
        if "player" in k.lower() or "team" in k.lower():
            print(f"  header/{k} = {json.dumps(hdr[k], ensure_ascii=False)[:200]}")
    for k, v in sorted(objs.items()):
        owner = v.get("owner", "?")
        print(f"  {k}: type={v.get('type', v.get('t','?'))} pos=({v.get('x')},{v.get('y')}) owner={owner}")
