#!/usr/bin/env python3
"""T06 图修复 + 1v1 duel 变体生成 (2026-09-06, 方案 A)

修复 4 张 T06 三类非法 identifier (与 T05 同套路, 修法照搬 fix_t05_maps_v3 验证过的模式):
  1. hero core:inham → 三蓝英雄分别 edric/iona/alchemist (options.type + portrait)
  2. resource core:resourceGold/Wood/Rare → core:gold/wood/crystal + 补 options.amount=8 (T05 同值)
  3. monster footman/pikeman("core: pikeman" 带空格)/cavalier/angel/blackKnight/hydra → swordsman, griffin → archer (数量不变)
     + monster options 补齐 aggression=guard / formation=wide (T05 标准, 防守卫不驻守变 roam)

duel 变体 (方案 A 核心思路: 只加大图轴, 不加多敌轴 — 一次一个难度轴):
  T06_adventure_72X72_01_duel.vmap = 72X72_01 去掉 hero_2/hero_3 + town_2/town_3 → 1v1 对角 (与 T05 结构一致)
"""
import os
import zipfile, json, glob, shutil

SRC_GLOB = os.environ.get("SRC_GLOB", '/mnt/d/Bigdata/hero3_fresh/Maps/training/T06_adventure_*.vmap')
RUNTIME = os.environ.get("RUNTIME", "/home/administrator/vcmi-native/rel/bin/data/Maps")
HERO_MAP = {"hero_1": "core:edric", "hero_2": "core:iona", "hero_3": "core:alchemist"}
RES_MAP = {"core:resourceGold": "core:gold", "core:resourceWood": "core:wood",
           "core:resourceRare": "core:crystal"}
MON_MAP = {"core:footman": "core:swordsman", "core:pikeman": "core:swordsman",
           "core:cavalier": "core:swordsman", "core:angel": "core:swordsman",
           "core:blackKnight": "core:swordsman", "core:hydra": "core:swordsman",
           "core:griffin": "core:archer"}
VALID_CREATURES = {'core:peasant', 'core:archer', 'core:swordsman'}
VALID_TOWN = {'core:dungeon', 'core:conflux'}
VALID_RES = {'core:gold', 'core:wood', 'core:crystal'}
VALID_HERO = {'core:edric', 'core:iona', 'core:christian'}  # 09-06 修正: alchemist 是职业名非英雄名


def load_vmap(p):
    z = zipfile.ZipFile(p)
    data = {n: z.read(n) for n in z.namelist()}
    z.close()
    return data


def save_vmap(p, data):
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, blob in data.items():
            zout.writestr(name, blob)


def fix_objects(objects):
    n_fix = {"hero": 0, "res": 0, "mon": 0}
    for k, o in objects.items():
        typ = o["type"]
        if typ == "hero" and o["options"].get("type") in ("core:inham",):
            nm = HERO_MAP.get(k, "core:edric")
            o["options"]["type"] = nm
            o["options"]["portrait"] = nm
            n_fix["hero"] += 1
        elif typ == "resource" and o.get("subtype") in RES_MAP:
            o["subtype"] = RES_MAP[o["subtype"]]
            o["options"].setdefault("amount", 8)
            n_fix["res"] += 1
        elif typ == "monster":
            st = str(o.get("subtype", "")).replace(": ", ":")  # 修 "core: pikeman" 冒号后带空格 bug
            if st in MON_MAP:
                o["subtype"] = MON_MAP[st]
                n_fix["mon"] += 1
            if "aggression" not in o["options"]:
                o["options"]["aggression"] = "guard"
            if "formation" not in o["options"]:
                o["options"]["formation"] = "wide"
    return n_fix


VALID_MINE = {'core:goldMine'}


def validate(objects):
    """返回非法 identifier 列表 (inspect_t06.py 同口径)"""
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

# ===== 1) 修复 4 张原图 =====
for p in sorted(glob.glob(SRC_GLOB)):
    if "_duel" in p:
        continue
    data = load_vmap(p)
    header = json.loads(data["header.json"])
    objects = json.loads(data["objects.json"])
    n_fix = fix_objects(objects)
    bad = validate(objects)
    assert not bad, f"{p} 修复后仍有非法 identifier: {bad}"
    data["header.json"] = json.dumps(header, ensure_ascii=False, indent=1).encode()
    data["objects.json"] = json.dumps(objects, ensure_ascii=False, indent=1).encode()
    save_vmap(p, data)
    shutil.copy(p, RUNTIME)
    print(f"OK {p.split('/')[-1]}: hero={n_fix['hero']} res={n_fix['res']} mon={n_fix['mon']}")

# ===== 2) 生成 duel 变体 (1v1: 删 hero_2/3 + town_2/3) =====
SRC = os.environ.get("SRC", '/mnt/d/Bigdata/hero3_fresh/Maps/training/T06_adventure_72X72_01.vmap')
DST = os.environ.get("DST", '/mnt/d/Bigdata/hero3_fresh/Maps/training/T06_adventure_72X72_01_duel.vmap')
DROP = {"hero_2", "hero_3", "town_2", "town_3"}

data = load_vmap(SRC)
header = json.loads(data["header.json"])
objects = json.loads(data["objects.json"])

for k in DROP:
    objects.pop(k, None)
# header.name 改名 (防 map 标签混淆)
try:
    header["name"] = "T06_adventure_72X72_01_duel"
except Exception:
    pass
bad = validate(objects)
assert not bad, f"duel 变体非法 identifier: {bad}"
heroes = {k: (v["options"].get("owner"), v["x"], v["y"]) for k, v in objects.items() if v["type"] == "hero"}
towns = {k: (v["options"].get("owner"), v["x"], v["y"]) for k, v in objects.items() if v["type"] == "town"}
assert len(heroes) == 2 and len(towns) == 2, f"duel 结构异常: heroes={heroes} towns={towns}"

data["header.json"] = json.dumps(header, ensure_ascii=False, indent=1).encode()
data["objects.json"] = json.dumps(objects, ensure_ascii=False, indent=1).encode()
save_vmap(DST, data)
shutil.copy(DST, RUNTIME)
print(f"OK duel: heroes={heroes} towns={towns}")

print("ALL DONE")
