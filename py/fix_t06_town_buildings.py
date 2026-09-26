#!/usr/bin/env python3
"""T06 图城镇补 built 兵巢 (09-27, 治 RECRUITED=0 第二层根因: T06 生成图 town 无 buildings)

参照 judgement_day_h3m (RECRUITED=33 已验证) 的 schema:
    options.buildings.allOf = ["core:dwellingLvl1", "core:dwellingLvl2", ...]

改动: 对每张 T06 图的【每个城镇】(红蓝对称) 若无 buildings 字段则补
    {"allOf": ["core:dwellingLvl1", "core:dwellingLvl2"]}
最小集: 只加 1/2 级兵巢 — 不动 hall(经济)/fort(防御)/tavern, 环境扰动最小。
幂等: 已有 buildings 的城镇跳过; 已处理过的图重跑无变化。
备份: <map>.bak_pre_dwell_0927 (首次处理时创建)。
原子写: 临时 zip + os.replace。

用法: python3 fix_t06_town_buildings.py <maps_dir>
默认 maps_dir=/mnt/d/Bigdata/hero3_fresh/maps/training
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
DWELLINGS = ["core:dwellingLvl1", "core:dwellingLvl2"]
SUFFIX = ".bak_pre_dwell_0927"


def patch_map(path):
    base = os.path.basename(path)
    bak = path + SUFFIX
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        payloads = {m.filename: z.read(m.filename) for m in members}
    objs = json.loads(payloads["objects.json"].decode("utf-8"))
    changed = 0
    towns = 0
    for k, o in objs.items():
        if not isinstance(o, dict) or "town" not in str(o.get("type", "")).lower():
            continue
        towns += 1
        opts = o.setdefault("options", {})
        if "buildings" in opts:
            continue
        opts["buildings"] = {"allOf": list(DWELLINGS)}
        changed += 1
    if changed == 0:
        print(f"  {base}: {towns} 城镇已有 buildings, 跳过 (幂等)")
        return False
    payloads["objects.json"] = json.dumps(objs, ensure_ascii=False, indent=1).encode("utf-8")
    tmp = path + ".tmp_dwell"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for m in members:
            zout.writestr(m.filename, payloads[m.filename])
    os.replace(tmp, path)
    print(f"  {base}: {changed}/{towns} 城镇补 dwellings ✅ (备份 {os.path.basename(bak)})")
    return True


def main():
    maps_dir = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/Bigdata/hero3_fresh/maps/training"
    print(f"maps_dir = {maps_dir}")
    ok = 0
    for m in MAPS:
        p = os.path.join(maps_dir, m)
        if not os.path.exists(p):
            print(f"  {m}: ❌ 不存在, 跳过")
            continue
        if patch_map(p):
            ok += 1
    print(f"\n完成: {ok}/{len(MAPS)} 张图有改动")


if __name__ == "__main__":
    main()
