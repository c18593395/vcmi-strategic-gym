#!/usr/bin/env python3
"""T04 同级镜像图生成 (2026-09-03)
触发: 观察窗复查触发条件①满足 (96ep 自发经济仍 0 + 行为固化依旧) — 用户拍板加图。
方案: 现有 6 张 T04 图各生成 1 张 180° 旋转变体 (terrain 行列反转 + 对象坐标变换),
      完全保留 0 守卫/城/矿/资源/英雄/胜利条件 = 同级同特征, 仅布局变化。
命名: T04_adventure_{W}X{H}_0{n}_mir.vmap (n=1→3, n=2→4)
运行: wsl bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/gen_t04_mirror.py"
"""
import zipfile, json, os, sys

SRC_DIR = "/mnt/d/Bigdata/hero3_fresh/maps/training"
SRC_MAPS = [
    "T04_adventure_20X20_01.vmap",
    "T04_adventure_20X20_02.vmap",
    "T04_adventure_30X30_01.vmap",
    "T04_adventure_30X30_02.vmap",
    "T04_adventure_36X36_01.vmap",
    "T04_adventure_36X36_02.vmap",
]

def rot180_terrain(grid):
    # 行列均反转 (180° 旋转)
    return [row[::-1] for row in grid[::-1]]

def rot180_xy(x, y, w, h):
    return (w - 1 - x, h - 1 - y)

def gen_mirror(src_name):
    src = os.path.join(SRC_DIR, src_name)
    base = src_name.replace(".vmap", "")
    # T04_adventure_20X20_01 → T04_adventure_20X20_03_mir
    suffix = "_01" if base.endswith("_01") else "_02"
    dst_base = base.replace(suffix, "_03_mir" if suffix == "_01" else "_04_mir")
    dst = os.path.join(SRC_DIR, dst_base + ".vmap")

    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        terrain = json.loads(zin.read("surface_terrain.json"))
        objects = json.loads(zin.read("objects.json"))

    h = len(terrain)
    w = len(terrain[0])
    new_terrain = rot180_terrain(terrain)

    new_objects = {}
    for key, o in objects.items():
        no = json.loads(json.dumps(o))  # deep copy
        nx, ny = rot180_xy(o["x"], o["y"], w, h)
        no["x"], no["y"] = nx, ny
        new_objects[key] = no

    header["name"] = dst_base
    header["description"] = f"{w}x{h} T04 mirror variant (rot180 of {base}), zero guards"

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
        zout.writestr("surface_terrain.json", json.dumps(new_terrain))
        zout.writestr("objects.json", json.dumps(new_objects, ensure_ascii=False, indent=1))

    # 自校验: 重读并核对对象数/坐标范围/地形行数
    with zipfile.ZipFile(dst) as zchk:
        ct = json.loads(zchk.read("surface_terrain.json"))
        co = json.loads(zchk.read("objects.json"))
        ch = json.loads(zchk.read("header.json"))
    assert len(ct) == h and len(ct[0]) == w, "terrain 尺寸错"
    for k, o in co.items():
        assert 0 <= o["x"] < w and 0 <= o["y"] < h, f"{k} 坐标越界"
    assert ch["name"] == dst_base, "名字错"
    n_town = sum(1 for o in co.values() if o["type"] == "town")
    n_hero = sum(1 for o in co.values() if o["type"] == "hero")
    print(f"OK {dst_base}: {w}x{h} towns={n_town} heroes={n_hero} objects={len(co)}")

if __name__ == "__main__":
    for m in SRC_MAPS:
        gen_mirror(m)
    print("ALL DONE: 6 mirror maps generated")
