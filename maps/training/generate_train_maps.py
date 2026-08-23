#!/usr/bin/env python3
"""生成简单训练地图 (.vmap 格式) — VCMI 兼容版 v2"""
import json, zipfile, os, argparse

GRASS = "wt00_"

def make_header(name, description, width, height):
    return {
        "name": name,
        "description": description,
        "difficulty": "NORMAL",
        "defeatIconIndex": 3,
        "mapLevels": {"surface": {"height": height, "width": width, "index": 0}},
        "players": {
            "red": {
                "canPlay": "PlayerOrAI",
                "heroes": {"header_hero_0": {"type": "core:edric"}},
                "mainHero": "header_hero_0",
                "team": -1
            },
            "blue": {
                "canPlay": "PlayerOrAI",
                "heroes": {"header_hero_1": {"type": "core:iona"}},
                "mainHero": "header_hero_1",
                "team": -1
            }
        },
        "victoryConditions": ["standardDefeat"],
        "allowedArtifacts": {"anyOf": []},
        "allowedSpells": {"anyOf": []},
        "mods": None
    }

def make_terrain(width, height):
    return [[GRASS] * width for _ in range(height)]

def make_objects(hero_x, hero_y, town_x, town_y, mine_x, mine_y):
    return {
        "hero_0": {
            "l": 0,
            "options": {
                "army": [{}, {}, {}, {"amount": 10, "type": "core:peasant"}, {}, {}, {}],
                "experience": 0, "formation": "wide", "owner": "red",
                "portrait": "core:edric", "type": "core:edric"
            },
            "subtype": "core:alchemist",
            "template": {
                "animation": "AH04_.def",
                "editorAnimation": "AH04_E.def",
                "mask": ["VVV", "VAV"],
                "visitableFrom": ["+++", "+-+", "+++"]
            },
            "type": "hero",
            "x": hero_x, "y": hero_y
        },
        "hero_1": {
            "l": 0,
            "options": {
                "army": [{}, {}, {}, {"amount": 5, "type": "core:peasant"}, {}, {}, {}],
                "experience": 0, "formation": "wide", "owner": "blue",
                "portrait": "core:iona", "type": "core:iona"
            },
            "subtype": "core:alchemist",
            "template": {
                "animation": "AH04_.def",
                "editorAnimation": "AH04_E.def",
                "mask": ["VVV", "VAV"],
                "visitableFrom": ["+++", "+-+", "+++"]
            },
            "type": "hero",
            "x": max(0, town_x - 2), "y": town_y
        },
        "town_0": {
            "l": 0,
            "options": {"formations": "random", "owner": "red"},
            "subtype": "core:castle",
            "template": {"animation": "", "mask": ["VVVVV", "VVAVV", "VVVVV"], "visitableFrom": ["+++++", "++-++", "+++++"]},
            "type": "town",
            "x": town_x, "y": town_y
        },
        "town_1": {
            "l": 0,
            "options": {"formations": "random", "owner": "blue"},
            "subtype": "core:dungeon",
            "template": {"animation": "", "mask": ["VVVVV", "VVAVV", "VVVVV"], "visitableFrom": ["+++++", "++-++", "+++++"]},
            "type": "town",
            "x": max(0, town_x - 2), "y": max(0, town_y - 3)
        },
        "mine_0": {
            "l": 0,
            "options": {"owner": None},
            "subtype": "core:goldMine",
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "mine",
            "x": mine_x, "y": mine_y
        }
    }

def generate_map(name, desc, width, height, hx, hy, tx, ty, mx, my, output_dir):
    header = make_header(name, desc, width, height)
    terrain = make_terrain(width, height)
    objects = make_objects(hx, hy, tx, ty, mx, my)
    
    filepath = os.path.join(output_dir, f"{name}.vmap")
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr("header.json", json.dumps(header, indent=2))
        z.writestr("surface_terrain.json", json.dumps(terrain))
        z.writestr("objects.json", json.dumps(objects, indent=2))
    
    print(f"Generated: {filepath}")
    return filepath

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="/mnt/d/Bigdata/hero3_fresh/Maps/training")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    maps = []
    
    maps.append(generate_map("T01_adventure_20X20_01", "20x20 no obstacles, hero near mine",
        20, 20, 5, 10, 3, 10, 15, 10, args.output_dir))
    maps.append(generate_map("T01_adventure_20X20_02", "20x20 no obstacles, hero far from mine",
        20, 20, 2, 2, 1, 2, 18, 18, args.output_dir))
    maps.append(generate_map("T01_adventure_30X30_01", "30x30 no obstacles, multiple targets",
        30, 30, 5, 15, 3, 15, 15, 15, args.output_dir))
    maps.append(generate_map("T01_adventure_30X30_02", "30x30 no obstacles, diagonal distance",
        30, 30, 2, 2, 1, 2, 28, 28, args.output_dir))
    maps.append(generate_map("T01_adventure_36X36_01", "36x36 no obstacles, standard size",
        36, 36, 5, 18, 3, 18, 30, 18, args.output_dir))
    
    print(f"\nGenerated {len(maps)} maps")
    for m in maps:
        print(f'  "{os.path.basename(m)}"')

if __name__ == "__main__":
    main()
