#!/usr/bin/env python3
"""T06 duel 变体矩阵备料 (2026-09-06, 任务 #2)

从已修复的 4 张 T06 原图生成 duel (1v1) 变体 — 只加大图轴不加多敌轴:
  72X72_02_duel / 108X108_01_duel / 108X108_02_duel (72X72_01_duel 已由 fix_t06_maps.py 生成)

每张: 去 hero_2/hero_3 + town_2/3 → 1 red (hero_0+town_0) vs 1 blue (hero_1+town_1) 对角。
只生成+inspect+同步副本, 不入 MAPS (等 duel 判据达标后择机入池)。
"""
import os
import zipfile, json, shutil

SRC_DIR = os.environ.get("SRC_DIR", '/mnt/d/Bigdata/hero3_fresh/Maps/training')
RUNTIME = os.environ.get("RUNTIME", "/home/administrator/vcmi-native/rel/bin/data/Maps")
DROP = {"hero_2", "hero_3", "town_2", "town_3"}
SOURCES = [
    "T06_adventure_72X72_02.vmap",
    "T06_adventure_108X108_01.vmap",
    "T06_adventure_108X108_02.vmap",
]

VALID_CREATURES = {'core:peasant', 'core:archer', 'core:swordsman'}
VALID_TOWN = {'core:dungeon', 'core:conflux'}
VALID_RES = {'core:gold', 'core:wood', 'core:crystal'}
VALID_MINE = {'core:goldMine'}
VALID_HERO = {'core:edric', 'core:iona', 'core:alchemist'}


def load_vmap(p):
    z = zipfile.ZipFile(p)
    data = {n: z.read(n) for n in z.namelist()}
    z.close()
    return data


def save_vmap(p, data):
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, blob in data.items():
            zout.writestr(name, blob)


def validate(objects):
    bad = []
    for k, v in objects.items():
        st = v.get("subtype", "")
        if v["type"] == "monster" and st not in VALID_CREATURES:
            bad.append(f"{k} monster {st}")
        elif v["type"] == "hero" and (v["options"].get("type") not in VALID_HERO
                                      or v["options"].get("portrait") not in VALID_HERO):
            bad.append(f"{k} hero {v['options'].get('type')}/{v['options'].get('portrait')}")
        elif v["type"] == "resource" and st not in VALID_RES:
            bad.append(f"{k} resource {st}")
        elif v["type"] == "town" and st not in VALID_TOWN:
            bad.append(f"{k} town {st}")
        elif v["type"] == "mine" and st not in VALID_MINE:
            bad.append(f"{k} mine {st}")
    return bad


for src_name in SOURCES:
    src = f"{SRC_DIR}/{src_name}"
    dst_name = src_name.replace(".vmap", "_duel.vmap")
    dst = f"{SRC_DIR}/{dst_name}"

    data = load_vmap(src)
    header = json.loads(data["header.json"])
    objects = json.loads(data["objects.json"])

    for k in DROP:
        objects.pop(k, None)
    try:
        header["name"] = dst_name.replace(".vmap", "")
    except Exception:
        pass

    bad = validate(objects)
    assert not bad, f"{dst_name} 非法 identifier: {bad}"
    heroes = {v["options"].get("owner"): (v["x"], v["y"]) for v in objects.values() if v["type"] == "hero"}
    towns = {v["options"].get("owner"): (v["x"], v["y"]) for v in objects.values() if v["type"] == "town"}
    assert len(heroes) == 2 and len(towns) == 2, f"{dst_name} 结构异常: {heroes} {towns}"

    data["header.json"] = json.dumps(header, ensure_ascii=False, indent=1).encode()
    data["objects.json"] = json.dumps(objects, ensure_ascii=False, indent=1).encode()
    save_vmap(dst, data)
    shutil.copy(dst, RUNTIME)
    print(f"OK {dst_name}: red{heroes['red']} vs blue{heroes['blue']} | towns red{towns['red']} blue{towns['blue']}")

print("ALL DONE (未入 MAPS, 备料完成)")
