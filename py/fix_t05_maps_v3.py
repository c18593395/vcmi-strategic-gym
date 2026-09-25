#!/usr/bin/env python3
"""T05 图修复 v3 (2026-09-03): hero_1 portrait/type core:inham (fork 不存在) → core:iona (T04 已验证)"""
import os
import zipfile, json, glob, shutil

RUNTIME = os.environ.get("RUNTIME", "/home/administrator/vcmi-native/rel/bin/data/Maps")
for p in sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_*.vmap')):
    z = zipfile.ZipFile(p)
    header = json.loads(z.read("header.json"))
    terrain = json.loads(z.read("surface_terrain.json"))
    objects = json.loads(z.read("objects.json"))
    z.close()

    for k, o in objects.items():
        if o["type"] == "hero" and o["options"].get("type") == "core:inham":
            o["options"]["type"] = "core:iona"
            o["options"]["portrait"] = "core:iona"

    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(objects, ensure_ascii=False, indent=1))

    with zipfile.ZipFile(p) as z:
        data = z.read("objects.json").decode('utf-8')
    assert 'inham' not in data.lower(), f"{p} 残留 inham"

    shutil.copy(p, RUNTIME)
    print(f"OK {p.split('/')[-1]}: inham→iona")

print("ALL DONE")
