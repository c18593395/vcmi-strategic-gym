"""
King of Pain.h3m.vmap (VCMI 完整格式) -> 精简训练格式

规则:
1. header 精简为 5 字段: {name, description, mapLevels, mods:[], players:[]}
2. surface_terrain.json 完全复用 (72x72 已匹配)
3. objects list -> dict, 按 type 前缀命名 hero_N/town_N/mine_N/resource_N/monster_N
4. 类型映射:
   - mine           -> mine_N    subtype='core:'+subtype, options.owner=null
   - resource       -> resource_N subtype='core:'+subtype, options.amount=默认值
   - randomTown     -> town_N    subtype='core:'+subtype, options.owner 保留
   - randomMonsterLevelN -> monster_N  subtype 按 level 映射, options.aggression='guard'
   - randomResource / treasureChest / 装饰类 -> 跳过
5. 合成 hero_0 (red, core:edric/core:alchemist) 放到 red 出生点
   - 从完整 header.players 里读出生点
"""
import zipfile, json, sys, re, shutil, os

# subtype 前缀: 精简格式统一带 'core:' 前缀
def _core(s):
    if s is None: return None
    s = str(s)
    return s if s.startswith("core:") else ("core:" + s)

# resource subtype -> 默认 amount
RESOURCE_AMOUNT = {
    "gold": 50, "wood": 8, "ore": 8, "mercury": 8, "sulfur": 8,
    "crystal": 8, "sapphire": 8, "amethyst": 8, "ruby": 8,
}

# randomMonsterLevelN -> 具体 subtype + amount + formation (对齐 T06 保守量)
MONSTER_LEVEL_MAP = {
    "randomMonsterLevel1": ("core:peasant",   20, "wide"),
    "randomMonsterLevel2": ("core:swordsman", 15, "wide"),
    "randomMonsterLevel3": ("core:archer",    12, "wide"),
    # 09-14 修: core:dragon 在 core mod 不存在 (只有 redDragon/blackDragon/greenDragon...),
    # 引擎 NEW_GAME 报 Failed to resolve identifier monster::core:dragon; 换三兽集 swordsman (可赢, 不叠强度轴)
    "randomMonsterLevel4": ("core:swordsman", 6,  "wide"),
    "randomMonsterLevel5": ("core:swordsman", 4,  "wide"),
}

# 装饰/跳过类型 (精简格式不需要)
SKIP_TYPES = {
    "mountain", "pineTrees", "oakTrees", "rock", "flowers", "shrub",
    "desertPalm", "desertBush", "tallGrass", "shortGrass", "stump",
    "volcano", "fence", "deadTree", "cave", "canyon", "bridge",
    "randomResource", "treasureChest", "artifact", "randomArtifact",
    "randomSpell", "randomCreature", "randomHero",
    "teleport", "prison", "graveyard", "shrine", "witchHut",
    "dungeon", "boat", "shipyard", "gate", "wall",
    "object", "objective", "resource",  # resource 单独处理
    "artifactShop", "blackMarket", "guild", "inn", "lighthouse",
    "market", "stable", "tower", "village", "warehouse",
    "magicSchool", "obstacle", "obstacleGroup", "resourceStack",
    "randomTown",  # 单独处理
    "monster",     # 单兵堆, King of Pain 无 (只有 randomMonsterLevel*)
    "hero",        # 单英雄, 精简格式需要生成
}

# 通用对象 template (3x3 mask, 与 T06 一致)
GENERIC_3X3_TEMPLATE = {
    "animation": "",
    "editorAnimation": None,
    "mask": ["VVV", "VAV", "VVV"],
    "visitableFrom": ["+++", "+-+", "+++"],
}

# 2x1 resource/mine template
GENERIC_RESOURCE_TEMPLATE = {
    "animation": "",
    "editorAnimation": None,
    "mask": ["VA"],
    "visitableFrom": ["+++", "+-+", "+++"],
}

def convert(src_vmap, dst_vmap, name="King of Pain"):
    """读取完整 vmap, 生成精简 vmap"""
    with zipfile.ZipFile(src_vmap) as z:
        full_header = json.loads(z.read("header.json"))
        full_objs = json.loads(z.read("objects.json"))
        terrain = json.loads(z.read("surface_terrain.json"))

    H = len(terrain)
    W = len(terrain[0])
    print(f"  地图尺寸: {W} x {H}")
    print(f"  完整对象数: {len(full_objs)}")

    # --- 1. 精简 header ---
    surface = full_header["mapLevels"]["surface"]
    slim_header = {
        "name": name,
        "description": full_header.get("description") or "",
        "mapLevels": {
            "surface": {
                "height": surface["height"],
                "width": surface["width"],
                "index": surface.get("index", 0),
            }
        },
        "mods": [],
        "players": [],
    }

    # --- 2. 生成 hero_0 (训练方 red, 放在 red 出生点) ---
    red_birth = full_header.get("players", {}).get("red", {}).get("mainTown", {})
    red_x = int(red_birth.get("x", 5))
    red_y = int(red_birth.get("y", 5))

    hero_0 = {
        "l": 0,
        "options": {
            "army": [
                {}, {}, {},
                {"amount": 15, "type": "core:peasant"},
                {}, {}, {},
            ],
            "experience": 0,
            "formation": "wide",
            "owner": "red",
            "portrait": "core:edric",
            "type": "core:edric",
        },
        "subtype": "core:alchemist",
        "template": {
            "animation": "AH04_.def",
            "editorAnimation": "AH04_E.def",
            "mask": ["VVV", "VAV"],
            "visitableFrom": ["+++", "+-+", "+++"],
        },
        "type": "hero",
        "x": red_x,
        "y": red_y,
    }

    slim_objs = {"hero_0": hero_0}

    # --- 3. 遍历完整对象, 按类型转换 ---
    counters = {"town": 0, "mine": 0, "resource": 0, "monster": 0}
    type_stats = {}
    skipped = 0

    for obj in full_objs:
        t = obj.get("type", "")
        type_stats[t] = type_stats.get(t, 0) + 1
        x = int(obj["x"])
        y = int(obj["y"])

        # --- town (来自 randomTown) ---
        if t == "randomTown":
            opts = obj.get("options") or {}
            owner = opts.get("owner")
            # subtype 可能为 'object' 占位符 (VCMI saveMap 不填 randomTown 真族系)
            # 回退链: obj['subtype'] (非占位符) -> options.availableFactions[0] -> 'dungeon' 兜底
            # T06 训练图惯例 = 每镇真族系 (castle/conflux/dungeon 等)
            sub = obj.get("subtype") or "dungeon"
            if sub == "object" or not sub:
                avail = opts.get("availableFactions") or []
                if isinstance(avail, list) and avail:
                    sub = str(avail[0])
                elif isinstance(avail, str) and avail:
                    sub = avail
                else:
                    sub = "dungeon"
            slim_town = {
                "l": 0,
                "options": {
                    "formations": "random",
                    "owner": owner,  # 保留 orange/blue/red 或 null
                },
                "subtype": _core(sub),
                "template": {
                    "animation": "",
                    "mask": ["VVVVV", "VVAVV", "VVVVV"],
                    "visitableFrom": ["+++++", "++-++", "+++++"],
                },
                "type": "town",
                "x": x,
                "y": y,
            }
            slim_objs[f"town_{counters['town']}"] = slim_town
            counters["town"] += 1
            continue

        # --- mine ---
        if t == "mine":
            slim_mine = {
                "l": 0,
                "options": {"owner": None},
                "subtype": _core(obj.get("subtype") or "goldMine"),
                "template": dict(GENERIC_3X3_TEMPLATE),
                "type": "mine",
                "x": x,
                "y": y,
            }
            slim_objs[f"mine_{counters['mine']}"] = slim_mine
            counters["mine"] += 1
            continue

        # --- resource ---
        if t == "resource":
            sub_raw = obj.get("subtype") or "gold"
            amount = RESOURCE_AMOUNT.get(sub_raw, 8)
            slim_res = {
                "l": 0,
                "options": {"amount": amount},
                "subtype": _core(sub_raw),
                "template": dict(GENERIC_RESOURCE_TEMPLATE),
                "type": "resource",
                "x": x,
                "y": y,
            }
            slim_objs[f"resource_{counters['resource']}"] = slim_res
            counters["resource"] += 1
            continue

        # --- randomMonsterLevelN ---
        if t in MONSTER_LEVEL_MAP:
            sub, amt, form = MONSTER_LEVEL_MAP[t]
            slim_mon = {
                "l": 0,
                "options": {
                    "amount": amt,
                    "aggression": "guard",
                    "formation": form,
                },
                "subtype": sub,
                "template": dict(GENERIC_3X3_TEMPLATE),
                "type": "monster",
                "x": x,
                "y": y,
            }
            slim_objs[f"monster_{counters['monster']}"] = slim_mon
            counters["monster"] += 1
            continue

        # --- 其他全部跳过 ---
        skipped += 1

    # --- 4. 写输出 zip ---
    with zipfile.ZipFile(dst_vmap, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("header.json", json.dumps(slim_header, indent=2, ensure_ascii=False))
        z.writestr("surface_terrain.json", json.dumps(terrain, separators=(",", ":")))
        z.writestr("objects.json", json.dumps(slim_objs, indent=2, ensure_ascii=False))

    print(f"  精简对象数: {len(slim_objs)}  (跳 {skipped} 装饰/杂类)")
    print(f"  counters: {counters}")
    print(f"  前 20 类 type: {dict(sorted(type_stats.items(), key=lambda kv:-kv[1])[:20])}")
    return len(slim_objs), counters

if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(os.path.basename(dst))[0]
    convert(src, dst, name=name)
    print(f"OK -> {dst}")
