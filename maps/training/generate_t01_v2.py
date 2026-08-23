#!/usr/bin/env python3
"""T01 地图生成 v2: 使用 train_v1.vmap 的精确对象模板"""
import json, zipfile, os

MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/Maps/training"
os.makedirs(MAP_DIR, exist_ok=True)
SRC = "/mnt/d/Bigdata/hero3_fresh/Maps/train_v1.vmap"

def get_templates():
    """从 train_v1.vmap 提取对象模板"""
    with zipfile.ZipFile(SRC) as zf:
        objects = json.loads(zf.read('objects.json'))
    templates = {}
    for k, v in objects.items():
        templates[k] = {
            "type": v["type"],
            "subtype": v["subtype"],
            "template": v["template"]
        }
    return templates

def make_header(name, desc, w, h):
    return {
        "name": name, "description": desc,
        "height": h, "width": w, "difficulty": "NORMAL", "levelLimit": 0,
        "players": [{"canComputerPlay": True, "canHumanPlay": True, "mainHero": None}],
        "version": 1,
        "mapLevels": {"surface": {"height": h, "width": w, "index": 0}}
    }

def make_objects(templates, hx, hy, mx, my, tx, ty):
    hero_t = templates["hero_0"]
    mine_t = templates["mine_0"]
    town_t = templates["town_0"]
    return {
        "hero_0": {
            "l": 0, "type": hero_t["type"], "subtype": hero_t["subtype"],
            "x": hx, "y": hy, "template": hero_t["template"],
            "options": {
                "owner": 0, "type": "core:edric",
                "primarySkills": {"attack": 2, "defense": 2, "spellPower": 1, "knowledge": 1},
                "experience": 0, "skills": [], "artifacts": {},
                "movement": 0, "mana": 10
            }
        },
        "mine_0": {
            "l": 0, "type": mine_t["type"], "subtype": mine_t["subtype"],
            "x": mx, "y": my, "template": mine_t["template"],
            "options": {"owner": None}
        },
        "town_0": {
            "l": 0, "type": town_t["type"], "subtype": town_t["subtype"],
            "x": tx, "y": ty, "template": town_t["template"],
            "options": {"owner": 0, "buildings": [], "hasFort": False}
        }
    }

def generate_map(templates, name, w, h, hx, hy, mx, my, tx, ty):
    header = make_header(name, f"{w}x{h} no obstacles, training map", w, h)
    terrain = [["gr24_"] * w for _ in range(h)]
    objects = make_objects(templates, hx, hy, mx, my, tx, ty)

    vmap_path = os.path.join(MAP_DIR, f"{name}.vmap")
    with zipfile.ZipFile(vmap_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("header.json", json.dumps(header, indent=2))
        zf.writestr("surface_terrain.json", json.dumps(terrain))
        zf.writestr("objects.json", json.dumps(objects, indent=2))
    return vmap_path

# T01 maps: no obstacles, hero at safe distance from edge
# Template sizes: hero 3x2, mine 3x3, town 5x3
# Safe margin: max(3, 5) + 1 = 6
maps = [
    ("T01_adventure_20X20_01", 20, 20, 9, 8, 15, 15, 8, 8),
    ("T01_adventure_20X20_02", 20, 20, 6, 6, 15, 15, 6, 9),
    ("T01_adventure_30X30_01", 30, 30, 10, 15, 25, 15, 10, 12),
    ("T01_adventure_30X30_02", 30, 30, 6, 6, 25, 25, 6, 9),
    ("T01_adventure_36X36_01", 36, 36, 10, 18, 30, 18, 10, 15),
]

if __name__ == "__main__":
    templates = get_templates()
    print(f"Templates loaded from {SRC}")
    for name, w, h, hx, hy, mx, my, tx, ty in maps:
        path = generate_map(templates, name, w, h, hx, hy, mx, my, tx, ty)
        print(f"Generated: {path}")
    print(f"\nTotal: {len(maps)} T01 maps")
