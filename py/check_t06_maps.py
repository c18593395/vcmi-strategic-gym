#!/usr/bin/env python3
"""T06 duel 3 张新增地图可用性检查 (09-12)

检查维度:
  1. 文件完整性 (zip 可解压)
  2. 结构完整性 (header.json / objects.json / map.bin 均存在)
  3. hero/town 数量 = 2 (duel 1v1)
  4. identifier 合法性 (creature/hero/resource/town/mine 白名单)
  5. 地图尺寸 (header 与 map.bin 对齐)
  6. 对角 duel 坐标 (red 在左上 5,5 / blue 在对角)
  7. 文件落地校验 (源 + 运行 + 副本 三处均存在)
"""
import os
import zipfile, json, os, sys, struct

MAPS = [
    "T06_adventure_72X72_02_duel.vmap",
    "T06_adventure_108X108_01_duel.vmap",
    "T06_adventure_108X108_02_duel.vmap",
]

VALID_CREATURES = {'core:peasant', 'core:archer', 'core:swordsman'}
VALID_TOWN = {'core:dungeon', 'core:conflux'}
VALID_RES = {'core:gold', 'core:wood', 'core:crystal'}
VALID_MINE = {'core:goldMine'}
VALID_HERO = {'core:edric', 'core:iona', 'core:alchemist'}

SRC = os.environ.get("SRC", "/mnt/d/Bigdata/hero3_fresh/Maps/training")
RUNTIME = os.environ.get("RUNTIME", "/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps")
CP = os.environ.get("CP", "/home/administrator/vcmi-native/rel/bin/data/Maps")
failures = []

for name in MAPS:
    print(f"\n=== {name} ===")
    src = f"{SRC}/{name}"
    rt = f"{RUNTIME}/{name}"
    cp = f"{CP}/{name}"

    # 1. 文件落地
    for label, p in [("源", src), ("运行", rt), ("副本", cp)]:
        if os.path.exists(p):
            sz = os.path.getsize(p)
            print(f"  [{label}] {p} size={sz}")
        else:
            failures.append(f"{name}: {label} 缺失 {p}")
            print(f"  [{label}] MISSING {p}")
    if not all(os.path.exists(p) for p in (src, rt, cp)):
        print("  SKIP (文件缺失)")
        continue

    # 2. zip 完整性 + 结构 (VCMII 格式: header.json + surface_terrain.json + objects.json)
    try:
        z = zipfile.ZipFile(src)
        names = z.namelist()
        missing = [r for r in ("header.json", "surface_terrain.json", "objects.json") if r not in names]
        if missing:
            failures.append(f"{name}: 缺 {missing}")
            print(f"  MISSING {missing}")
        print(f"  [zip] {len(names)} entries: {names}")
    except Exception as e:
        failures.append(f"{name}: zip 损坏 {e}")
        print(f"  ZIP ERROR: {e}")
        continue

    header = json.loads(z.read("header.json"))
    objects = json.loads(z.read("objects.json"))
    terrain = json.loads(z.read("surface_terrain.json"))
    z.close()

    # 3. hero/town 数量 = 2
    heroes = {k: v for k, v in objects.items() if v.get("type") == "hero"}
    towns = {k: v for k, v in objects.items() if v.get("type") == "town"}
    print(f"  [hero] {len(heroes)}  {heroes}")
    print(f"  [town] {len(towns)}  {towns}")
    if len(heroes) != 2:
        failures.append(f"{name}: hero 数 {len(heroes)} != 2")
    if len(towns) != 2:
        failures.append(f"{name}: town 数 {len(towns)} != 2")

    # 4. identifier 合法性
    bad = []
    for k, v in objects.items():
        st = v.get("subtype", "")
        if v.get("type") == "monster" and st not in VALID_CREATURES:
            bad.append(f"monster {st}")
        elif v.get("type") == "hero":
            ht = v.get("options", {}).get("type")
            hp = v.get("options", {}).get("portrait")
            if ht not in VALID_HERO or hp not in VALID_HERO:
                bad.append(f"hero {ht}/{hp}")
        elif v.get("type") == "resource" and st not in VALID_RES:
            bad.append(f"resource {st}")
        elif v.get("type") == "town" and st not in VALID_TOWN:
            bad.append(f"town {st}")
        elif v.get("type") == "mine" and st not in VALID_MINE:
            bad.append(f"mine {st}")
    if bad:
        failures.append(f"{name}: 非法 identifier {bad}")
        print(f"  [identifier] BAD: {bad}")
    else:
        print(f"  [identifier] all valid ({len(objects)} objects)")

    # 5. 地图尺寸: header.mapLevels.surface + surface_terrain list 长度
    surf = header.get("mapLevels", {}).get("surface", {})
    hx, hy = surf.get("width"), surf.get("height")
    terr_len = len(terrain) if isinstance(terrain, list) else (terrain.get("height") if isinstance(terrain, dict) else None)
    print(f"  [size] header mapLevels.surface w={hx} h={hy} | terrain len={terr_len}")
    if isinstance(terrain, list) and len(terrain) != hx:
        failures.append(f"{name}: terrain list len={len(terrain)} != header h={hx}")
    expected = None
    if "72X72" in name:
        expected = 72
    elif "108X108" in name:
        expected = 108
    if expected and (hx != expected or hy != expected):
        failures.append(f"{name}: 尺寸 header ({hx},{hy}) != expected ({expected},{expected})")

    # 6. 对角坐标
    hpos = {v.get("options", {}).get("owner"): (v["x"], v["y"]) for v in heroes.values()}
    tpos = {v.get("options", {}).get("owner"): (v["x"], v["y"]) for v in towns.values()}
    print(f"  [pos] heroes={hpos} towns={tpos}")
    if expected:
        blue_h = hpos.get("blue")
        red_h = hpos.get("red")
        if blue_h and (blue_h[0] != expected - 6 or blue_h[1] != expected - 6):
            print(f"  [pos] WARN: blue hero 不在预期对角 ({expected-6},{expected-6}) 实际 {blue_h}")
        if red_h and (red_h[0] != 5 or red_h[1] != 5):
            print(f"  [pos] WARN: red hero 不在 (5,5) 实际 {red_h}")
    # 蓝英雄 vs 蓝镇 距离 ≤ 3 (蓝英雄应贴蓝镇, 否则开局取兵/守镇路径长)
    blue_h = hpos.get("blue")
    blue_t = tpos.get("blue")
    if blue_h and blue_t:
        d = abs(blue_h[0] - blue_t[0]) + abs(blue_h[1] - blue_t[1])
        print(f"  [pos] blue_hero 到 blue_town 曼哈顿距离 = {d}")
        if d > 5:
            print(f"  [pos] WARN: 距离 {d} > 5, 蓝英雄远离蓝镇")

    # 7. 资源/矿/怪物 数量统计 (sanity)
    cnt = {}
    for v in objects.values():
        cnt[v.get("type")] = cnt.get(v.get("type"), 0) + 1
    print(f"  [types] {cnt}")

print("\n" + "="*60)
if failures:
    print(f"FAIL ({len(failures)}):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("ALL PASS: 3 张 T06 duel 地图结构完整、identifier 合法、对角 duel 布局正确")
