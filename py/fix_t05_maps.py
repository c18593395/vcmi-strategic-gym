#!/usr/bin/env python3
"""T05 图加载修复 (2026-09-03): core:footman 在当前 VCMI fork 不存在 → 替换 core:swordsman
(战力近似同 tier 近战; peasant/archer/swordsman 均已实测存在)
修复 4 张 T05 图, 写回 Maps/training 并同步 rel/bin/data/Maps/ 运行时路径
"""
import zipfile, json, glob, shutil

BAD, GOOD = "core:footman", "core:swordsman"
RUNTIME = "/home/administrator/vcmi-native/rel/bin/data/Maps"

for p in sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_*.vmap')):
    z = zipfile.ZipFile(p)
    header = json.loads(z.read("header.json"))
    terrain = json.loads(z.read("surface_terrain.json"))
    objects = json.loads(z.read("objects.json"))
    z.close()

    n = 0
    for k, o in objects.items():
        if o.get("subtype") == BAD:
            o["subtype"] = GOOD
            n += 1

    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(objects, ensure_ascii=False, indent=1))

    # 回读校验: 无残留 footman
    with zipfile.ZipFile(p) as z:
        o2 = json.loads(z.read("objects.json"))
    assert not any(o.get("subtype") == BAD for o in o2.values()), f"{p} 仍有 footman"

    shutil.copy(p, RUNTIME)
    print(f"OK {p.split('/')[-1]}: 替换 {n} 处 footman→swordsman")

print("ALL DONE (4 maps fixed + runtime synced)")
