#!/usr/bin/env python3
"""T05 图扩充 (2026-09-05): ①可用 3 图镜像变体 ②36X36_02 守卫调低回归
镜像: 180° 旋转 (terrain 反转+对象坐标变换), 守卫同步旋转难度不变 — T04_mir 同款方案
调守卫: 36X36_02 swordsman 8→4 / archer 10→5 / peasant 15→8 (可赢难度)
产出 4 张新图 → Maps/training + rel/bin/data/Maps 双路径 (踩坑 #143 事实 2)
"""
import zipfile, json, glob, shutil, os

SRC_DIR = "/mnt/d/Bigdata/hero3_fresh/Maps/training"
RUNTIME = "/home/administrator/vcmi-native/rel/bin/data/Maps"

def rot180_terrain(grid):
    return [row[::-1] for row in grid[::-1]]

# ---- ① 镜像变体 ----
for src_name in ["T05_adventure_36X36_01.vmap", "T05_adventure_52X52_01.vmap", "T05_adventure_52X52_02.vmap"]:
    src = os.path.join(SRC_DIR, src_name)
    base = src_name.replace(".vmap", "")
    dst_base = base + "_mir"
    dst = os.path.join(SRC_DIR, dst_base + ".vmap")

    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        terrain = json.loads(zin.read("surface_terrain.json"))
        objects = json.loads(zin.read("objects.json"))

    h, w = len(terrain), len(terrain[0])
    new_terrain = rot180_terrain(terrain)
    new_objects = {}
    for k, o in objects.items():
        no = json.loads(json.dumps(o))
        no["x"], no["y"] = w - 1 - o["x"], h - 1 - o["y"]
        new_objects[k] = no
    header["name"] = dst_base
    header["description"] = f"{w}x{h} T05 mirror variant (rot180 of {base})"

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
        zout.writestr("surface_terrain.json", json.dumps(new_terrain))
        zout.writestr("objects.json", json.dumps(new_objects, ensure_ascii=False, indent=1))

    with zipfile.ZipFile(dst) as z:
        o = json.loads(z.read("objects.json"))
        t = json.loads(z.read("surface_terrain.json"))
    assert len(t) == h and len(t[0]) == w
    for k, o2 in o.items():
        assert 0 <= o2["x"] < w and 0 <= o2["y"] < h, f"{k} 越界"
    shutil.copy(dst, RUNTIME)
    print(f"OK 镜像 {dst_base}: {w}x{h} objects={len(o)}")

# ---- ② 36X36_02 守卫调低 (原图直接改, 原文件覆盖前备份到 backups 语义由 git 承担) ----
p = os.path.join(SRC_DIR, "T05_adventure_36X36_02.vmap")
with zipfile.ZipFile(p) as zin:
    header = json.loads(zin.read("header.json"))
    terrain = json.loads(zin.read("surface_terrain.json"))
    objects = json.loads(zin.read("objects.json"))

HALVE = {"core:swordsman": 4, "core:archer": 5, "core:peasant": 8}
for k, o in objects.items():
    if o["type"] == "monster":
        old = o["options"]["amount"]
        o["options"]["amount"] = HALVE.get(o["subtype"], max(1, old // 2))
        print(f"  36X36_02 {k} {o['subtype']}: {old}→{o['options']['amount']}")
header["description"] = "36X36 T05, guards halved for winnable difficulty (09-05)"

with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
    zout.writestr("surface_terrain.json", json.dumps(terrain))
    zout.writestr("objects.json", json.dumps(objects, ensure_ascii=False, indent=1))
shutil.copy(p, RUNTIME)
print("OK 36X36_02 守卫减半回归")
print("ALL DONE: +3 镜像 +1 调守卫 = 轮换 3→7 张")
