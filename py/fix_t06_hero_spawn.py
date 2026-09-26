#!/usr/bin/env python3
"""T06 图英雄出生位置 → 己方城上 (09-27 v3 地图修复: 引擎 init 直接置 visiting, 零几何依赖)
沿用项目历史验证约定 (T7.5 S2 时代 T05 英雄"出生在城上", RECRUITED=13.2/局)。
幂等 + 备份 .bak_spawn_0927 + 原子写。
用法: python3 fix_t06_hero_spawn.py [maps_dir]
"""
import json
import zipfile
import os
import sys
import shutil

MAPS = [
    "T06_adventure_72X72_01_duel.vmap",
    "T06_adventure_72X72_01.vmap",
    "T06_adventure_72X72_02_duel.vmap",
    "T06_adventure_72X72_02.vmap",
    "T06_adventure_108X108_02_duel.vmap",
    "T06_adventure_108X108_02.vmap",
]
SUFFIX = ".bak_spawn_0927"


def patch_map(path):
    base = os.path.basename(path)
    bak = path + SUFFIX
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        payloads = {m.filename: z.read(m.filename) for m in members}
    objs = json.loads(payloads["objects.json"].decode("utf-8"))
    # 收集城: owner → pos
    towns = {}
    heroes_changed = 0
    heroes_total = 0
    for k, o in objs.items():
        if isinstance(o, dict) and "town" in str(o.get("type", "")).lower():
            owner = o.get("options", {}).get("owner")
            towns.setdefault(owner, (o.get("x"), o.get("y")))
    for k, o in objs.items():
        if not (isinstance(o, dict) and "hero" in str(o.get("type", "")).lower()):
            continue
        heroes_total += 1
        owner = o.get("options", {}).get("owner")
        if owner in towns:
            tx, ty = towns[owner]
            if (o.get("x"), o.get("y")) != (tx, ty):
                o["x"], o["y"] = tx, ty
                heroes_changed += 1
    if heroes_changed == 0:
        print(f"  {base}: {heroes_total} 英雄已在城上, 跳过 (幂等)")
        return False
    payloads["objects.json"] = json.dumps(objs, ensure_ascii=False, indent=1).encode("utf-8")
    tmp = path + ".tmp_spawn"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for m in members:
            zout.writestr(m.filename, payloads[m.filename])
    os.replace(tmp, path)
    print(f"  {base}: {heroes_changed}/{heroes_total} 英雄移到城上 ✅ (备份 {os.path.basename(bak)})")
    return True


def main():
    maps_dir = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/Bigdata/hero3_fresh/maps/training"
    print(f"maps_dir = {maps_dir}")
    changed = 0
    for m in MAPS:
        p = os.path.join(maps_dir, m)
        if not os.path.exists(p):
            print(f"  {m}: ❌ 不存在")
            continue
        if patch_map(p):
            changed += 1
    print(f"\n完成: {changed}/{len(MAPS)} 张图改动")


if __name__ == "__main__":
    main()
