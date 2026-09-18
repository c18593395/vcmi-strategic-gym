#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BUILD P1 备料探针 v4: 完整对比 T04 (参照, 有 fort+L1) 与 T05/T06 (待改) 的全部城对象 JSON。只读。"""
import json
import zipfile

MAPS = [("T04参照", "/mnt/d/Bigdata/hero3_fresh/maps/training/T04_adventure_20X20_01.vmap"),
        ("T05_36", "/mnt/d/Bigdata/hero3_fresh/maps/training/T05_adventure_36X36_01.vmap"),
        ("T06_72", "/mnt/d/Bigdata/hero3_fresh/maps/training/T06_adventure_72X72_02.vmap")]

for tag, p in MAPS:
    print(f"\n===== {tag} =====")
    with zipfile.ZipFile(p) as z:
        data = json.loads(z.read("objects.json"))
    towns = {k: v for k, v in data.items() if k.startswith("town") or v.get("type") == "town"}
    print(f"城对象: {list(towns.keys())}")
    for k, v in towns.items():
        print(f"--- {k} ---")
        print(json.dumps(v, ensure_ascii=False, indent=1))
