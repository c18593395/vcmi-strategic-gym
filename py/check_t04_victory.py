#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 T04 vmap 的引擎胜利/失败条件定义 (header.json)"""
import json, zipfile, glob, os

KEYS = ["victory", "loss", "win", "defeat", "trigger", "condition", "event"]
for p in sorted(glob.glob("/mnt/d/Bigdata/hero3_fresh/maps/training/T04_adventure_20X20_01.vmap")) + \
         sorted(glob.glob("/mnt/d/Bigdata/hero3_fresh/maps/training/T03_adventure_20X20_01.vmap")):
    name = os.path.basename(p)
    print(f"===== {name}")
    with zipfile.ZipFile(p) as z:
        print("  zip 内容:", z.namelist())
        for fn in z.namelist():
            if fn.endswith(".json"):
                try:
                    d = json.loads(z.read(fn))
                except Exception as e:
                    print(f"  [{fn}] 解析失败: {e}"); continue
                def walk(o, path=""):
                    if isinstance(o, dict):
                        for k, v in o.items():
                            kl = k.lower()
                            if any(t in kl for t in KEYS):
                                print(f"  [{fn}] {path}/{k} = {json.dumps(v, ensure_ascii=False)[:300]}")
                            walk(v, f"{path}/{k}")
                    elif isinstance(o, list):
                        for i, v in enumerate(o):
                            walk(v, f"{path}[{i}]")
                walk(d)
