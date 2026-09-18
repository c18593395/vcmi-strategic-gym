#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BUILD P1 备料: 给在池非 duel 图的红城预置 fort + dwellingLvl1 (options.buildings.all)。
生成 <名>_p1.vmap 副本, 不改原文件不入池 (错窗纪律: 地图轴, 等窗改名切换 + sync_maps --strict)。
JSON 写法依据 CGTownInstance::serializeJsonOptions (L1107 buildingsLIC / all 数组 addBuilding)。
dungeon 建筑 jsonKey: core:fort / core:dwellingLvl1 (config/factions/dungeon.json, dwellingLvl1 requires fort)。"""
import json
import shutil
import zipfile

MAPS_DIR = "/mnt/d/Bigdata/hero3_fresh/maps/training"
TARGETS = [
    "T05_adventure_36X36_01.vmap",
    "T05_adventure_52X52_02.vmap",
    "T06_adventure_72X72_01.vmap",
    "T06_adventure_72X72_02.vmap",
    "T06_adventure_108X108_02.vmap",
]
BUILD_ALL = ["core:fort", "core:dwellingLvl1"]

for name in TARGETS:
    src = f"{MAPS_DIR}/{name}"
    dst = f"{MAPS_DIR}/{name.replace('.vmap', '_p1.vmap')}"
    with zipfile.ZipFile(src) as z:
        objs = json.loads(z.read("objects.json"))
    n_red = 0
    for k, v in objs.items():
        if k.startswith("town") and v.get("type") == "town" and v.get("options", {}).get("owner") == "red":
            opts = v.setdefault("options", {})
            opts["buildings"] = {"all": BUILD_ALL, "none": []}
            n_red += 1
    if n_red == 0:
        print(f"[skip] {name}: 无红城")
        continue
    # 重建 zip: 复制原条目, 替换 objects.json
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "objects.json":
                zout.writestr(item, json.dumps(objs, ensure_ascii=False))
            else:
                zout.writestr(item, zin.read(item.filename))
    print(f"[ok] {name} -> {dst.rsplit('/', 1)[-1]} (红城 x{n_red} 预置 {BUILD_ALL})")
