#!/usr/bin/env python3
# check_map_towns.py — T04 六图城镇坐标/owner 清单 (09-02 晚, 双城几何陷阱验证)
# 用法: wsl python3 /mnt/d/Bigdata/hero3_fresh/py/check_map_towns.py
import zipfile, json, glob

for p in sorted(glob.glob("/mnt/d/Bigdata/hero3_fresh/maps/training/*")):
    name = p.split("/")[-1]
    try:
        with zipfile.ZipFile(p) as z:
            objs = json.loads(z.read("objects.json"))
        towns = []
        for k, o in objs.items():
            if k.startswith("town_"):
                towns.append((k, o["x"], o["y"], str(o.get("options", {}).get("owner", ""))))
        print(name, towns)
    except Exception as e:
        print(name, "ERR", e)
