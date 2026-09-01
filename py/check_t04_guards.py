#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 T04 六图的守卫/城镇/资源配置 (2026-08-29 晋级后验证)"""
import json, zipfile, glob, os

for p in sorted(glob.glob("/mnt/d/Bigdata/hero3_fresh/maps/training/T04_adventure_*.vmap")):
    name = os.path.basename(p)
    try:
        with zipfile.ZipFile(p) as z:
            objs = json.loads(z.read("objects.json"))
        guards = [(int(v["x"]), int(v["y"]), v.get("l", 0)) for k, v in objs.items() if k.startswith("monster_")]
        towns = [(k, int(v["x"]), int(v["y"])) for k, v in objs.items() if "town" in k.lower()]
        mines = [(k, int(v["x"]), int(v["y"])) for k, v in objs.items() if "mine" in k.lower()]
        res = [(k, int(v["x"]), int(v["y"])) for k, v in objs.items()
               if k.startswith("resource_")]
        print(f"== {name}")
        print(f"  守卫 x{len(guards)}: {guards}")
        print(f"  城镇 x{len(towns)}: {towns}")
        print(f"  矿 x{len(mines)}: {mines}")
        print(f"  资源堆 x{len(res)}")
    except Exception as e:
        print(f"== {name}  ERROR: {e}")
