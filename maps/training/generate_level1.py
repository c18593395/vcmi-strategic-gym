#!/usr/bin/env python3
"""Level 1 地图生成: 有障碍物, 资源分散, 英雄需绕路"""
import json, zipfile, os, random

MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/Maps/training"
os.makedirs(MAP_DIR, exist_ok=True)

GRASS = "gr24_"
WATER = "wt00_"
ROCK = "ro14_"
DIRT = "dt01_"

def make_header(name, desc, w, h):
    return {
        "name": name, "description": desc,
        "height": h, "width": w, "difficulty": 0, "levelLimit": 0,
        "players": [
            {"canComputerPlay": True, "canHumanPlay": True, "mainHero": None},
            {"canComputerPlay": True, "canHumanPlay": True, "mainHero": None}
        ],
        "version": 1
    }

def make_terrain(w, h, obstacles):
    """Create terrain grid with obstacles. obstacles = list of (x, y, terrain_type)"""
    grid = []
    for y in range(h):
        row = []
        for x in range(w):
            tile = {"terrain": GRASS, "objects": []}
            for ox, oy, ot in obstacles:
                if ox == x and oy == y:
                    tile["terrain"] = ot
                    break
            row.append(tile)
        grid.append(row)
    return grid

def place_obstacles(w, h, density, hero_pos, mine_pos, town_pos):
    """Generate random obstacle positions avoiding hero/mine/town areas"""
    obstacles = []
    protected = set()
    # Protect hero area (3x3)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            protected.add((hero_pos[0]+dx, hero_pos[1]+dy))
    # Protect mine area (3x3)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            protected.add((mine_pos[0]+dx, mine_pos[1]+dy))
    # Protect town area (3x3)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            protected.add((town_pos[0]+dx, town_pos[1]+dy))

    num_obstacles = int(w * h * density)
    attempts = 0
    while len(obstacles) < num_obstacles and attempts < num_obstacles * 10:
        x = random.randint(0, w-1)
        y = random.randint(0, h-1)
        if (x, y) not in protected:
            terrain = random.choice([ROCK, WATER, ROCK])  # More rocks than water
            obstacles.append((x, y, terrain))
            protected.add((x, y))  # Don't double-place
        attempts += 1
    return obstacles

def generate_map(name, desc, w, h, hero_pos, mine_pos, town_pos, obstacle_density, seed):
    random.seed(seed)
    obstacles = place_obstacles(w, h, obstacle_density, hero_pos, mine_pos, town_pos)
    terrain = make_terrain(w, h, obstacles)

    # 确保不超出边界 (模板至少 4 格)
    hero_pos = (max(4, min(w-5, hero_pos[0])), max(4, min(h-5, hero_pos[1])))
    mine_pos = (max(4, min(w-5, mine_pos[0])), max(4, min(h-5, mine_pos[1])))
    town_pos = (max(4, min(w-5, town_pos[0])), max(4, min(h-5, town_pos[1])))

    objects = {}

    # Hero (red)
    objects["hero_0"] = {
        "l": 0, "type": "hero", "subtype": "core:alchemist",
        "x": hero_pos[0], "y": hero_pos[1],
        "template": {"animation": "AH04_.def", "editorAnimation": "AH04_E.def",
                     "mask": ["VVV", "VAV"], "visitableFrom": ["+++", "+-+"], "terrains": []},
        "options": {"owner": 0, "type": "core:edric",
                    "primarySkills": {"attack": 2, "defense": 2, "spellPower": 1, "knowledge": 1},
                    "experience": 0, "skills": [], "artifacts": {},
                    "movement": 0, "mana": 10}
    }

    # Gold mine (neutral)
    objects["mine_0"] = {
        "l": 0, "type": "mine", "subtype": "core:goldMine",
        "x": mine_pos[0], "y": mine_pos[1],
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"],
                     "visitableFrom": ["+++", "+-+", "+++"], "terrains": []},
        "options": {"owner": None}
    }

    # Town (red)
    objects["town_0"] = {
        "l": 0, "type": "town", "subtype": "core:castle",
        "x": town_pos[0], "y": town_pos[1],
        "template": {"animation": "", "mask": ["VVVV", "VVVV", "VAVV"],
                     "visitableFrom": ["++++", "++++", "+-++", "++++"], "terrains": []},
        "options": {"owner": 0, "buildings": [], "hasFort": False}
    }

    # Convert terrain to flat list for vmap format
    terrain_flat = []
    for row in terrain:
        for tile in row:
            terrain_flat.append(tile["terrain"])

    header = make_header(name, desc, w, h)
    vmap_path = os.path.join(MAP_DIR, f"{name}.vmap")
    with zipfile.ZipFile(vmap_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("header.json", json.dumps(header, indent=2))
        zf.writestr("surface_terrain.json", json.dumps(terrain_flat))
        zf.writestr("objects.json", json.dumps(objects, indent=2))

    return vmap_path

# Level 1 maps: obstacles at varying densities
maps = [
    # (name, w, h, hero_xy, mine_xy, town_xy, density, seed)
    ("L1_adventure_20X20_01", 20, 20, (3, 10), (16, 10), (3, 7), 0.10, 101),
    ("L1_adventure_20X20_02", 20, 20, (2, 2), (18, 18), (2, 5), 0.12, 102),
    ("L1_adventure_20X20_03", 20, 20, (10, 3), (10, 17), (7, 3), 0.15, 103),
    ("L1_adventure_30X30_01", 30, 30, (5, 15), (25, 15), (5, 12), 0.10, 104),
    ("L1_adventure_30X30_02", 30, 30, (3, 3), (27, 27), (3, 6), 0.12, 105),
    ("L1_adventure_30X30_03", 30, 30, (15, 5), (15, 25), (12, 5), 0.15, 106),
    ("L1_adventure_36X36_01", 36, 36, (5, 18), (30, 18), (5, 15), 0.10, 107),
    ("L1_adventure_36X36_02", 36, 36, (3, 3), (33, 33), (3, 6), 0.12, 108),
]

if __name__ == "__main__":
    for name, w, h, hero, mine, town, density, seed in maps:
        path = generate_map(name, f"Level 1: obstacles density={density}", w, h, hero, mine, town, density, seed)
        print(f"Generated: {path} ({w}x{h}, density={density})")
    print(f"\nTotal: {len(maps)} Level 1 maps")
