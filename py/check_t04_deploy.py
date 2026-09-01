#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比 T04 部署副本 (引擎实际加载) vs 源 maps/training 的 hero/mine/town 坐标 (2026-08-29 [MINE] step0 排查)"""
import json, zipfile, glob, os

for d in ["/home/administrator/vcmi-native/rel/bin/data/Maps", "/mnt/d/Bigdata/hero3_fresh/maps/training"]:
    print(f"##### {d}")
    for p in sorted(glob.glob(d + "/T04_adventure_*.vmap")):
        with zipfile.ZipFile(p) as z:
            o = json.loads(z.read("objects.json"))
        items = []
        for k in sorted(o):
            if k.startswith(("hero", "mine", "town")):
                items.append(f"{k}={o[k]['x']},{o[k]['y']}")
        print(f"  {os.path.basename(p)}: {' '.join(items)}")
