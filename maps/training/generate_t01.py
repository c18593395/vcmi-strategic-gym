#!/usr/bin/env python3
"""T01 地图生成: 无障碍, 1 hero + 1 mine + 1 town, 单人"""
import json, zipfile, os

MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/Maps/training"
os.makedirs(MAP_DIR, exist_ok=True)

def make_header(name, desc, w, h):
    return {
        "name": name, "description": desc,
        "height": h, "width": w, "difficulty": "NORMAL", "levelLimit": 0,
        "players": [{"canComputerPlay": True, "canHumanPlay": True, "mainHero": None}],
        "version": 1,
        "mapLevels": {"surface": {"height": h, "width": w, "index": 0}}
    }

def make_objects(hx, hy, mx, my, tx, ty):
    return {
        "hero_0": {
            "l": 0, "type": "hero", "subtype": "core:alchemist",
            "x": hx, "y": hy,
            "template": {
                "animation": "AH04_.def", "editorAnimation": "AH04_E.def",
                "mask": ["VVV", "VAV"], "visitableFrom": ["+++", "+-+"], "terrains": []
            },
            "options": {
                "owner": 0, "type": "core:edric",
                "primarySkills": {"attack": 2, "defense": 2, "spellPower": 1, "knowledge": 1},
                "experience": 0, "skills": [], "artifacts": {},
                "movement": 0, "mana": 10
            }
        },
        "mine_0": {
            "l": 0, "type": "mine", "subtype": "core:goldMine",
            "x": mx, "y": my,
            "template": {
                "animation": "", "mask": ["VVV", "VAV", "VVV"],
                "visitableFrom": ["+++", "+-+", "+++"], "terrains": []
            },
            "options": {"owner": None}
        },
        "town_0": {
            "l": 0, "type": "town", "subtype": "core:castle",
            "x": tx, "y": ty,
            "template": {
                "animation": "", "mask": ["VVVV", "VVVV", "VAVV"],
                "visitableFrom": ["++++", "++++", "+-++", "++++"], "terrains": []
            },
            "options": {"owner": 0, "buildings": [], "hasFort": False}
        }
    }

def generate_map(name, w, h, hx, hy, mx, my, tx, ty):
    header = make_header(name, f"{w}x{h} no obstacles, training map", w, h)
    terrain = [["gr24_"] * w for _ in range(h)]
    objects = make_objects(hx, hy, mx, my, tx, ty)

    vmap_path = os.path.join(MAP_DIR, f"{name}.vmap")
    with zipfile.ZipFile(vmap_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("header.json", json.dumps(header, indent=2))
        zf.writestr("surface_terrain.json", json.dumps(terrain))
        zf.writestr("objects.json", json.dumps(objects, indent=2))
    return vmap_path

# T01 maps: no obstacles, hero at safe distance from edge
maps = [
    ("T01_adventure_20X20_01", 20, 20, 9, 8, 15, 15, 8, 8),
    ("T01_adventure_20X20_02", 20, 20, 5, 5, 15, 15, 5, 8),
    ("T01_adventure_30X30_01", 30, 30, 10, 15, 25, 15, 10, 12),
    ("T01_adventure_30X30_02", 30, 30, 5, 5, 25, 25, 5, 8),
    ("T01_adventure_36X36_01", 36, 36, 10, 18, 30, 18, 10, 15),
]

if __name__ == "__main__":
    for name, w, h, hx, hy, mx, my, tx, ty in maps:
        path = generate_map(name, w, h, hx, hy, mx, my, tx, ty)
        print(f"Generated: {path}")
    print(f"\nTotal: {len(maps)} T01 maps")
