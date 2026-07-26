#!/usr/bin/env python3
"""Generate a minimal vmap with 2 towns + 2 heroes on flat grass terrain."""
import json, zipfile, os, sys

SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 48
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 42
OUT = sys.argv[3] if len(sys.argv) > 3 else f"/mnt/d/Bigdata/hero3_fresh/maps/s1-minimal-{SEED}.vmap"

import random
random.seed(SEED)

# Header
header = {
    "allowedArtifacts": {"anyOf": []},
    "defeatIconIndex": 3,
    "description": f"Minimal training map {SIZE}x{SIZE} seed={SEED}",
    "difficulty": "EASY",
    "mapLevels": {"surface": {"height": SIZE, "width": SIZE}},
    "mods": [],
    "name": f"Minimal-{SEED}",
    "players": {
        "red": {"canPlay": "PlayerOrAI", "heroes": {}},
        "blue": {"canPlay": "PlayerOrAI", "heroes": {}},
    },
    "victoryConditions": [],
    "triggeredEvents": [],
    "versionMajor": 1,
    "versionMinor": 0,
    "victoryIconIndex": 0,
}

# Surface terrain (flat grass)
terrain = ["gd00_" for _ in range(SIZE * SIZE)]

# Objects
objects = {}

TOWN_TYPES = ["core:castle", "core:rampart", "core:tower", "core:necropolis"]
HERO_TYPES = {"red": ["core:orrin", "core:christian", "core:sorsha", "core:cragHack", "core:gundula"],
              "blue": ["core:orrin", "core:christian", "core:sorsha", "core:cragHack", "core:gundula"]}

MARGIN = 3
sep = SIZE // 4

for pi, (player, color_idx) in enumerate([("red", 0), ("blue", 1)]):
    # Place town in player quadrant
    if player == "red":
        tx, ty = random.randint(MARGIN, sep - MARGIN), random.randint(MARGIN, SIZE - MARGIN - 1)
    else:
        tx, ty = random.randint(SIZE - sep - MARGIN, SIZE - MARGIN - 1), random.randint(MARGIN, SIZE - MARGIN - 1)
    
    ttype = random.choice(TOWN_TYPES)
    tid = f"town_{pi}"
    objects[tid] = {
        "l": 0, "x": tx, "y": ty,
        "type": "town", "subtype": ttype,
        "template": {"animation": "", "mask": ["VVVVV", "VVAVV", "VVVVV"], "visitableFrom": ["+++++", "++-++", "+++++"]}
    }
    header["players"][player]["heroes"][f"header_hero_{pi}"] = {"type": random.choice(HERO_TYPES[player])}
    
    # Place hero adjacent to town
    dirs = [(1,0),(0,1),(-1,0),(0,-1)]
    for dx, dy in dirs:
        hx, hy = tx + dx, ty + dy
        if MARGIN <= hx < SIZE - MARGIN and MARGIN <= hy < SIZE - MARGIN:
            break
    hid = f"hero_{pi}"
    objects[hid] = {
        "l": 0, "x": hx, "y": hy,
        "portrait": 2,
        "type": "hero", "subtype": random.choice(HERO_TYPES[player]),
        "template": {"animation": "", "mask": ["VVV", "VAV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "options": {"experience": 1}
    }

# Write vmap (ZIP of 3 JSONs)
zobj = zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED)
zobj.writestr("header.json", json.dumps(header, indent=2, ensure_ascii=False))
zobj.writestr("surface_terrain.json", json.dumps([list(row) for row in [terrain[i*SIZE:(i+1)*SIZE] for i in range(SIZE)]], ensure_ascii=False))
zobj.writestr("objects.json", json.dumps(objects, indent=2, ensure_ascii=False))
zobj.close()

total = len(objects) + 2  # towns + heroes
print(f"Generated: {OUT}")
print(f"  Size: {SIZE}x{SIZE}, {os.path.getsize(OUT)//1024}KB")
print(f"  Objects: {total}")
print(f"  Seed: {SEED}")
