#!/usr/bin/env python3
"""09-14 King_of_Pain_h3m.vmap: core:dragon(4个, 引擎不存在该id) -> core:swordsman
根因: vcmi_full_to_slim.py MONSTER_LEVEL_MAP 把 randomMonsterLevel4/5 映射成 core:dragon
(引擎报 Failed to resolve identifier monster::core:dragon, NEW_GAME 失败)
替换为图内已在用的 core:swordsman (三兽集, 守卫可赢, 不叠强度轴)。
备份: King_of_Pain_h3m.vmap.bak_dragon_0914
"""
import json, zipfile, shutil, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    r"d:\Bigdata\hero3_fresh\maps\training\King_of_Pain_h3m.vmap"
BAK = SRC + ".bak_dragon_0914"
NEW_SUB = "core:swordsman"
BAD = "core:dragon"

if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)
    print("backup ->", BAK)

zin = zipfile.ZipFile(SRC, "r")
names = zin.namelist()
data = {n: zin.read(n) for n in names}
zin.close()

objs = json.loads(data["objects.json"])
hit = []
for key, o in objs.items():
    if o.get("type") == "monster" and o.get("subtype") == BAD:
        o["subtype"] = NEW_SUB
        hit.append((key, o["x"], o["y"], o.get("options", {}).get("amount")))
assert len(hit) == 4, f"期望4个 dragon, 实际 {len(hit)}"

data["objects.json"] = json.dumps(objs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
tmp = SRC + ".tmp"
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
    for n in names:
        z.writestr(n, data[n])
os.replace(tmp, SRC)

# 校验
z = zipfile.ZipFile(SRC)
chk = json.loads(z.read("objects.json"))
left = sum(1 for o in chk.values() if o.get("subtype") == BAD)
sw = sum(1 for o in chk.values() if o.get("subtype") == NEW_SUB)
print("替换 %d 个: %s" % (len(hit), hit))
print("校验: 残留 dragon=%d, swordsman 总数=%d, 条目=%s" % (left, sw, z.namelist()))
