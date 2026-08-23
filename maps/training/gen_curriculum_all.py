#!/usr/bin/env python3
"""
课程学习地图统一重生成 (2026-08-23)
按 train_v1.vmap 的 VCMI 兼容格式 (dict players, red+blue 双玩家) 重建 T01-T04。
T05/T06 的 dict 版已可用, 不覆盖。
修复: 旧 T01-T04 是 list players 数组格式 (mainHero=None) -> VCMI 引擎加载即 core dump。
"""
import json, zipfile, os, random, shutil

SRC = "D:/Bigdata/hero3_fresh/maps/train_v1.vmap"
DST = "D:/Bigdata/hero3_fresh/Maps/training"
os.makedirs(DST, exist_ok=True)

random.seed(20260823)

# ---------- 模板 ----------
OBJ_TEMPLATE = {
    "mine": {
        "l": 0, "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine",
    },
    "resource_gold": {
        "l": 0, "options": {"amount": 8},
        "subtype": "core:gold",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "resource",
    },
    "resource_wood": {
        "l": 0, "options": {"amount": 8},
        "subtype": "core:wood",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "resource",
    },
    "resource_rare": {
        "l": 0, "options": {"amount": 8},
        "subtype": "core:crystal",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "resource",
    },
    "monster": {
        "l": 0, "options": {"amount": 8, "aggression": "guard", "formation": "wide"},
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "monster",
    },
}

def load_template():
    with zipfile.ZipFile(SRC) as z:
        header = json.loads(z.read("header.json"))
        objects = json.loads(z.read("objects.json"))
    # header: dict players 保留 (red/blue + header_hero_0/1 + mainHero + team)
    return header, objects

def make_header(name, desc, w, h):
    header, _ = load_template()
    header["name"] = name
    header["description"] = desc
    header["mapLevels"] = {"surface": {"height": h, "width": w, "index": 0}}
    # 只保留 standardDefeat, 去掉 specialVictory (100 gold 提前胜利会干扰训练)
    header["victoryConditions"] = ["standardDefeat"]
    header.pop("triggeredEvents", None)
    header["mods"] = {}
    # hero 标识符必须与 objects.json 一致且为 VCMI 标准英雄 (train_v1 的 blue core:inham 不存在 → 加载崩)
    header["players"]["red"]["heroes"]["header_hero_1"]["type"] = "core:edric"
    header["players"]["blue"]["heroes"]["header_hero_0"]["type"] = "core:iona"
    return header

def _protected_points(w, h, cfg):
    """所有对象位置 + blue 固定位置, 障碍必须避开"""
    pts = set()
    for kx, ky in [("hero_x","hero_y"), ("town_x","town_y"), ("mine_x","mine_y")]:
        pts.add((cfg[kx], cfg[ky]))
    for rx, ry, _rt in cfg.get("resources", []):
        pts.add((rx, ry))
    for mx, my, _st, _am in cfg.get("monsters", []):
        pts.add((mx, my))
    pts.add((w - 4, h - 4))  # blue hero
    pts.add((w - 3, h - 2))  # blue town
    return pts

def make_terrain_grass(w, h, cfg=None):
    return [["gr24_"] * w for _ in range(h)]

def make_terrain_mix(w, h, cfg):
    """Level 1: 全草地 (wt00_/rc00_ 非草地地形在当前 VCMI 加载 segfault, 待查; 先用对象布局提供难度)"""
    return [["gr24_"] * w for _ in range(h)]

def make_terrain_guarded(w, h, cfg):
    """Level 2: 同 Level 1 地形 (弱野怪守矿)"""
    return make_terrain_mix(w, h, cfg)

def make_terrain_economy(w, h, cfg):
    """Level 3: 全草地 (非草地地形 segfault 待查)"""
    return [["gr24_"] * w for _ in range(h)]

def set_obj(obj, x, y, **kw):
    o = dict(obj)
    o["x"], o["y"] = x, y
    o.update(kw)
    return o

def build_objects(w, h, cfg, level):
    """cfg: dict(hero_x, hero_y, town_x, town_y, mine_x, mine_y, resources=[(x,y,type)], monsters=[(x,y,subtype,amount)])
    ⚠️ red town 的 template mask 是 5x3 (anchor 居中) → town_x ∈ [2, w-3], town_y ∈ [1, h-2], 否则越界 segfault
    hero 必须避开 town mask 区域 (|dx|<=2 且 |dy|<=1)"""
    _, src_objects = load_template()
    objects = {}

    # red town: clamp 到 mask 安全区
    tx = max(2, min(cfg["town_x"], w - 3))
    ty = max(1, min(cfg["town_y"], h - 2))
    # red hero: 避开 town mask (|hx-tx|<=2 且 |hy-ty|<=1 则挪)
    hx, hy = cfg["hero_x"], cfg["hero_y"]
    guard = 0
    while abs(hx - tx) <= 2 and abs(hy - ty) <= 1 and guard < 20:
        hx = (hx + 4) % (w - 2) + 1
        hy = (hy + 3) % (h - 2) + 1
        guard += 1
    assert abs(hx - tx) > 2 or abs(hy - ty) > 1, f"hero 无法避开 town mask w={w} h={h}"
    cfg = dict(cfg); cfg["town_x"], cfg["town_y"] = tx, ty
    cfg["hero_x"], cfg["hero_y"] = hx, hy

    # red hero (player 0, 左下)
    hero0 = dict(src_objects["hero_0"])
    hero0["x"], hero0["y"] = cfg["hero_x"], cfg["hero_y"]
    hero0["options"] = dict(hero0.get("options", {}))
    hero0["options"]["owner"] = "red"
    # Level 2+: 英雄带 2-3 级兵 (footman/griffin); Level 0-1: peasant
    if level >= 2:
        hero0["options"]["army"] = [{}, {}, {}, {"amount": 8, "type": "core:swordsman"}, {}, {}, {}]
    else:
        hero0["options"]["army"] = [{}, {}, {}, {"amount": 10, "type": "core:peasant"}, {}, {}, {}]
    objects["hero_0"] = hero0

    # blue hero (右上, 弱) — train_v1 的 core:inham 不存在, 改用 core:iona
    bhx, bhy = w - 4, h - 4
    btx, bty = w - 3, h - 2   # town mask 5x3: x∈[w-5,w-1], y∈[h-3,h-1] 界内 (w,h>=20)
    hero1 = dict(src_objects["hero_1"])
    hero1["x"], hero1["y"] = bhx, bhy
    hero1["options"] = dict(hero1.get("options", {}))
    hero1["options"]["owner"] = "blue"
    hero1["options"]["type"] = "core:iona"
    hero1["options"]["portrait"] = "core:iona"
    hero1["options"]["army"] = [{}, {}, {}, {"amount": 5, "type": "core:peasant"}, {}, {}, {}]
    objects["hero_1"] = hero1

    # red town
    town0 = dict(src_objects["town_0"])
    town0["x"], town0["y"] = cfg["town_x"], cfg["town_y"]
    town0["options"] = dict(town0.get("options", {}))
    town0["options"]["owner"] = "red"
    objects["town_0"] = town0

    # blue town
    town1 = dict(src_objects["town_1"])
    town1["x"], town1["y"] = btx, bty
    town1["options"] = dict(town1.get("options", {}))
    town1["options"]["owner"] = "blue"
    objects["town_1"] = town1

    # mine (中立)
    objects["mine_0"] = set_obj(OBJ_TEMPLATE["mine"], cfg["mine_x"], cfg["mine_y"])

    # resources
    for i, (rx, ry, rtype) in enumerate(cfg.get("resources", [])):
        key = f"resource_{i}"
        objects[key] = set_obj(OBJ_TEMPLATE[f"resource_{rtype}"], rx, ry)

    # monsters
    for i, (mx2, my2, subtype, amount) in enumerate(cfg.get("monsters", [])):
        m = dict(OBJ_TEMPLATE["monster"])
        m["subtype"] = subtype
        m["options"] = {"amount": amount, "aggression": "guard", "formation": "wide"}
        objects[f"monster_{i}"] = set_obj(m, mx2, my2)

    return objects

def generate(name, desc, w, h, cfg, level, terrain_fn):
    header = make_header(name, desc, w, h)
    terrain = terrain_fn(w, h, cfg)
    objects = build_objects(w, h, cfg, level)
    path = os.path.join(DST, f"{name}.vmap")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("header.json", json.dumps(header, indent=2))
        z.writestr("surface_terrain.json", json.dumps(terrain))
        z.writestr("objects.json", json.dumps(objects, indent=2))
    # 校验
    with zipfile.ZipFile(path) as z:
        h2 = json.loads(z.read("header.json"))
        assert isinstance(h2["players"], dict), f"{name} players not dict!"
        assert "red" in h2["players"] and "blue" in h2["players"], f"{name} missing red/blue"
        o2 = json.loads(z.read("objects.json"))
        for k in ["hero_0", "hero_1", "town_0", "town_1", "mine_0"]:
            assert k in o2, f"{name} missing {k}"
        # 校验: 所有对象界内 (mask 3x3 或 5x3 需留边)
        for k, v in o2.items():
            x, y = v.get("x"), v.get("y")
            assert x is not None and 1 <= x <= w - 2 and 1 <= y <= h - 2, f"{name} {k} 越界 ({x},{y}) w={w} h={h}"
    print(f"OK  {name}  {w}x{h}  level={level}  hero=({cfg['hero_x']},{cfg['hero_y']}) town=({cfg['town_x']},{cfg['town_y']}) mine=({cfg['mine_x']},{cfg['mine_y']})")
    return path

# ---------- 地图定义 ----------
MAPS = []

# Level 0: T01 无障碍基础 (5 张)
t01 = [
    ("T01_adventure_20X20_01", 20, 20, {"hero_x": 5, "hero_y": 10, "town_x": 3, "town_y": 10, "mine_x": 15, "mine_y": 10, "resources": []}),
    ("T01_adventure_20X20_02", 20, 20, {"hero_x": 2, "hero_y": 2, "town_x": 1, "town_y": 2, "mine_x": 18, "mine_y": 18, "resources": []}),
    ("T01_adventure_30X30_01", 30, 30, {"hero_x": 5, "hero_y": 15, "town_x": 3, "town_y": 15, "mine_x": 25, "mine_y": 15, "resources": []}),
    ("T01_adventure_30X30_02", 30, 30, {"hero_x": 2, "hero_y": 2, "town_x": 1, "town_y": 2, "mine_x": 28, "mine_y": 28, "resources": []}),
    ("T01_adventure_36X36_01", 36, 36, {"hero_x": 5, "hero_y": 18, "town_x": 3, "town_y": 18, "mine_x": 30, "mine_y": 18, "resources": []}),
]
for name, w, h, cfg in t01:
    MAPS.append((name, w, h, cfg, 0, make_terrain_grass))

# Level 1: T02 地形混合+多资源 (6 张)
t02 = [
    ("T02_adventure_20X20_01", 20, 20, {"hero_x": 2, "hero_y": 2, "town_x": 1, "town_y": 2, "mine_x": 15, "mine_y": 15, "resources": [(5, 5, "gold"), (10, 3, "wood"), (18, 10, "rare")]}),
    ("T02_adventure_20X20_02", 20, 20, {"hero_x": 18, "hero_y": 18, "town_x": 18, "town_y": 17, "mine_x": 3, "mine_y": 3, "resources": [(5, 15, "gold"), (15, 5, "wood"), (10, 10, "rare")]}),
    ("T02_adventure_30X30_01", 30, 30, {"hero_x": 3, "hero_y": 3, "town_x": 1, "town_y": 3, "mine_x": 25, "mine_y": 25, "resources": [(10, 10, "gold"), (20, 5, "wood"), (15, 20, "rare"), (25, 5, "gold")]}),
    ("T02_adventure_30X30_02", 30, 30, {"hero_x": 27, "hero_y": 27, "town_x": 27, "town_y": 26, "mine_x": 3, "mine_y": 3, "resources": [(5, 25, "gold"), (25, 5, "wood"), (15, 15, "rare")]}),
    ("T02_adventure_36X36_01", 36, 36, {"hero_x": 3, "hero_y": 3, "town_x": 1, "town_y": 3, "mine_x": 30, "mine_y": 30, "resources": [(10, 10, "gold"), (20, 5, "wood"), (15, 25, "rare"), (30, 5, "gold")]}),
    ("T02_adventure_36X36_02", 36, 36, {"hero_x": 33, "hero_y": 33, "town_x": 33, "town_y": 32, "mine_x": 3, "mine_y": 3, "resources": [(5, 30, "gold"), (30, 5, "wood"), (18, 18, "rare")]}),
]
for name, w, h, cfg in t02:
    MAPS.append((name, w, h, cfg, 1, make_terrain_mix))

# Level 2: T03 弱野怪守矿 (6 张)
t03 = [
    ("T03_adventure_20X20_01", 20, 20, {"hero_x": 2, "hero_y": 2, "town_x": 1, "town_y": 2, "mine_x": 15, "mine_y": 15, "resources": [(10, 5, "gold")], "monsters": [(14, 14, "core:peasant", 8), (15, 13, "core:archer", 6)]}),
    ("T03_adventure_20X20_02", 20, 20, {"hero_x": 18, "hero_y": 18, "town_x": 18, "town_y": 17, "mine_x": 3, "mine_y": 3, "resources": [(5, 15, "gold")], "monsters": [(4, 4, "core:peasant", 8), (3, 5, "core:archer", 6)]}),
    ("T03_adventure_30X30_01", 30, 30, {"hero_x": 3, "hero_y": 3, "town_x": 1, "town_y": 3, "mine_x": 25, "mine_y": 25, "resources": [(10, 10, "gold"), (20, 5, "wood")], "monsters": [(24, 24, "core:peasant", 10), (25, 23, "core:archer", 8), (20, 20, "core:swordsman", 4)]}),
    ("T03_adventure_30X30_02", 30, 30, {"hero_x": 27, "hero_y": 27, "town_x": 27, "town_y": 26, "mine_x": 3, "mine_y": 3, "resources": [(5, 25, "gold")], "monsters": [(4, 4, "core:peasant", 10), (3, 5, "core:archer", 8)]}),
    ("T03_adventure_36X36_01", 36, 36, {"hero_x": 3, "hero_y": 3, "town_x": 1, "town_y": 3, "mine_x": 30, "mine_y": 30, "resources": [(10, 10, "gold"), (20, 5, "wood"), (15, 25, "rare")], "monsters": [(29, 29, "core:peasant", 12), (30, 28, "core:archer", 8), (25, 25, "core:swordsman", 5)]}),
    ("T03_adventure_36X36_02", 36, 36, {"hero_x": 33, "hero_y": 33, "town_x": 33, "town_y": 32, "mine_x": 3, "mine_y": 3, "resources": [(5, 30, "gold")], "monsters": [(4, 4, "core:peasant", 12), (3, 5, "core:archer", 8)]}),
]
for name, w, h, cfg in t03:
    MAPS.append((name, w, h, cfg, 2, make_terrain_guarded))

# Level 3: T04 城镇经济 (6 张)
t04 = [
    ("T04_adventure_20X20_01", 20, 20, {"hero_x": 2, "hero_y": 2, "town_x": 1, "town_y": 2, "mine_x": 15, "mine_y": 15, "resources": [(5, 5, "gold"), (10, 3, "wood"), (12, 12, "rare"), (8, 8, "gold")]}),
    ("T04_adventure_20X20_02", 20, 20, {"hero_x": 18, "hero_y": 18, "town_x": 18, "town_y": 17, "mine_x": 3, "mine_y": 3, "resources": [(5, 15, "gold"), (15, 5, "wood"), (10, 10, "rare")]}),
    ("T04_adventure_30X30_01", 30, 30, {"hero_x": 3, "hero_y": 3, "town_x": 1, "town_y": 3, "mine_x": 25, "mine_y": 25, "resources": [(10, 10, "gold"), (20, 5, "wood"), (15, 20, "rare"), (8, 8, "gold"), (22, 22, "wood")]}),
    ("T04_adventure_30X30_02", 30, 30, {"hero_x": 27, "hero_y": 27, "town_x": 27, "town_y": 26, "mine_x": 3, "mine_y": 3, "resources": [(5, 25, "gold"), (25, 5, "wood"), (15, 15, "rare"), (10, 20, "gold")]}),
    ("T04_adventure_36X36_01", 36, 36, {"hero_x": 3, "hero_y": 3, "town_x": 1, "town_y": 3, "mine_x": 30, "mine_y": 30, "resources": [(10, 10, "gold"), (20, 5, "wood"), (15, 25, "rare"), (8, 8, "gold"), (25, 15, "wood")]}),
    ("T04_adventure_36X36_02", 36, 36, {"hero_x": 33, "hero_y": 33, "town_x": 33, "town_y": 32, "mine_x": 3, "mine_y": 3, "resources": [(5, 30, "gold"), (30, 5, "wood"), (18, 18, "rare"), (10, 25, "gold")]}),
]
for name, w, h, cfg in t04:
    MAPS.append((name, w, h, cfg, 3, make_terrain_economy))

def main():
    print(f"重新生成 {len(MAPS)} 张课程地图 -> {DST}")
    for name, w, h, cfg, level, terrain_fn in MAPS:
        generate(name, f"Curriculum Level {level} training map {w}x{h}", w, h, cfg, level, terrain_fn)
    print("完成")

if __name__ == "__main__":
    main()
