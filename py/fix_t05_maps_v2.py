#!/usr/bin/env python3
"""T05 图修复 v2 (2026-09-03): resource subtype 映射 + amount 补齐
core:resourceGold→core:gold / core:resourceWood→core:wood / core:resourceRare→core:crystal
(T04 已验证可加载的类型; resourceRare 语义 = 稀有矿 → crystal)
"""
import os
import zipfile, json, glob, shutil

MAP_SUB = {
    "core:resourceGold": "core:gold",
    "core:resourceWood": "core:wood",
    "core:resourceRare": "core:crystal",
}
RUNTIME = os.environ.get("RUNTIME", "/home/administrator/vcmi-native/rel/bin/data/Maps")
for p in sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_*.vmap')):
    z = zipfile.ZipFile(p)
    header = json.loads(z.read("header.json"))
    terrain = json.loads(z.read("surface_terrain.json"))
    objects = json.loads(z.read("objects.json"))
    z.close()

    n = 0
    for k, o in objects.items():
        if o["type"] == "resource":
            old = o.get("subtype")
            if old in MAP_SUB:
                o["subtype"] = MAP_SUB[old]
                n += 1
            if "amount" not in o.get("options", {}) or not o["options"].get("amount"):
                o["options"]["amount"] = 8

    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(objects, ensure_ascii=False, indent=1))

    with zipfile.ZipFile(p) as z:
        o2 = json.loads(z.read("objects.json"))
    bad = [o.get("subtype") for o in o2.values() if o.get("subtype", "").startswith("core:resource")]
    assert not bad, f"{p} 残留坏类型 {bad}"

    shutil.copy(p, RUNTIME)
    print(f"OK {p.split('/')[-1]}: resource 替换 {n} 处 + amount 补齐")

print("ALL DONE")
