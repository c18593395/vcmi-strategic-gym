#!/usr/bin/env python3
"""hero_3 alchemist→christian 修复 (09-06): 引擎报 "Couldn't resolve hero identifier core:alchemist" —
alchemist 是职业名 (hero subtype 字段) 而非英雄名, fix_t06_maps.py 初版误用作英雄名。
只影响带 hero_3 的 4 张原图 (duel 变体已删 hero_2/3 不受影响)。无需停训 — 引擎每局启动读文件。"""
import zipfile, json, glob, shutil

SRC_GLOB = '/mnt/d/Bigdata/hero3_fresh/Maps/training/T06_adventure_*.vmap'
RUNTIME = "/home/administrator/vcmi-native/rel/bin/data/Maps"


def load_vmap(p):
    z = zipfile.ZipFile(p)
    data = {n: z.read(n) for n in z.namelist()}
    z.close()
    return data


def save_vmap(p, data):
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, blob in data.items():
            zout.writestr(name, blob)


for p in sorted(glob.glob(SRC_GLOB)):
    data = load_vmap(p)
    objects = json.loads(data["objects.json"])
    changed = 0
    for k, o in objects.items():
        if o["type"] == "hero" and o["options"].get("type") == "core:alchemist":
            o["options"]["type"] = "core:christian"
            o["options"]["portrait"] = "core:christian"
            changed += 1
    if changed:
        data["objects.json"] = json.dumps(objects, ensure_ascii=False, indent=1).encode()
        save_vmap(p, data)
        shutil.copy(p, RUNTIME)
    print(f"{'OK' if changed else 'SKIP'} {p.split('/')[-1]}: alchemist→christian x{changed}")

print("ALL DONE")
