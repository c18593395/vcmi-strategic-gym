#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P9 验证: T03 训练图是否双雄无城 (决定"击杀守卫=淘汰"是否成立)"""
import zipfile, json

for m in ["T03_adventure_20X20_01.vmap", "T03_adventure_30X30_01.vmap"]:
    p = f"/mnt/d/Bigdata/hero3_fresh/Maps/training/{m}"
    z = zipfile.ZipFile(p)
    h = json.loads(z.read("header.json"))
    print("==", m, "| zip entries:", z.namelist())

    def find(d, key, out, path=""):
        if isinstance(d, dict):
            for k, v in d.items():
                if key in k.lower():
                    out.append((path + k, v if not isinstance(v, (dict, list)) else
                                (f"list×{len(v)}" if isinstance(v, list) else "dict")))
                find(v, key, out, path + k + ".")
        elif isinstance(d, list):
            for i, v in enumerate(d[:20]):
                find(v, key, out, path + f"[{i}].")

    towns, heroes, owner = [], [], []
    find(h, "town", towns)
    find(h, "hero", heroes)
    find(h, "owner", owner)
    print("  towns:", towns[:8])
    print("  heroes:", heroes[:8])
    print("  owner:", owner[:12])
