import json, zipfile, os, random

# Level 1 map generation script
# Based on gen_v3.py, adds terrain mix and multiple resource points

src = "D:/Bigdata/hero3_fresh/Maps/train_v1.vmap"
dst_dir = "D:/Bigdata/hero3_fresh/Maps/training"
os.makedirs(dst_dir, exist_ok=True)

# Terrain codes (assuming from train_v1.vmap)
# wt = water (impassable), gr = grass (passable), ro = rock (impassable), sa = sand (passable?), dt = dirt (passable?)
# We'll use: gr24_ (grass), wt00_ (water), ro00_ (rock), rd00_ (road, need to verify)
# For now, use gr24_ for grass, wt00_ for water, ro00_ for rock, and assume rd00_ is road.
# If rd00_ doesn't work, we can adjust later.

# Level 1 map definitions: (name, w, h, hero_x, hero_y, mine_x, mine_y, resource_points)
# resource_points: list of (x, y, type) where type in ['gold', 'wood', 'rare', 'chest']
level1_maps = [
    ("T02_adventure_20X20_01", 20, 20, 2, 2, 15, 15, [(5,5,'gold'), (10,3,'wood'), (18,10,'rare'), (12,18,'chest')]),
    ("T02_adventure_20X20_02", 20, 20, 18, 18, 3, 3, [(5,15,'gold'), (15,5,'wood'), (10,10,'rare')]),
    ("T02_adventure_30X30_01", 30, 30, 3, 3, 25, 25, [(10,10,'gold'), (20,5,'wood'), (15,20,'rare'), (25,15,'chest')]),
    ("T02_adventure_30X30_02", 30, 30, 27, 27, 3, 3, [(5,25,'gold'), (25,5,'wood'), (15,15,'rare')]),
    ("T02_adventure_36X36_01", 36, 36, 3, 3, 30, 30, [(10,10,'gold'), (20,5,'wood'), (15,25,'rare'), (30,15,'chest')]),
    ("T02_adventure_36X36_02", 36, 36, 33, 33, 3, 3, [(5,30,'gold'), (30,5,'wood'), (18,18,'rare')]),
]

for name, w, h, hx, hy, mx, my, resources in level1_maps:
    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        terrain = json.loads(zin.read("surface_terrain.json"))
        objects = json.loads(zin.read("objects.json"))
    
    header["name"] = name
    header["description"] = f"{w}x{h} terrain mix, multiple resources, training map"
    header["mapLevels"] = {"surface": {"height": h, "width": w, "index": 0}}
    
    # Generate terrain: mostly grass, some water, rock, and roads
    terrain = []
    for y in range(h):
        row = []
        for x in range(w):
            # Default grass
            tile = "gr24_"
            # Add water rivers (horizontal and vertical lines)
            if (x == 5 and 3 <= y <= h-4) or (y == 5 and 3 <= x <= w-4):
                tile = "wt00_"
            # Add rock mountains (diagonal lines)
            if (x == y and 2 <= x <= min(w-3, h-3)) or (x == w-1-y and 2 <= x <= min(w-3, h-3)):
                tile = "ro00_"
            # Add roads (from hero to mine, and to some resources)
            if (hx <= x <= mx and y == hy) or (x == hx and hy <= y <= my):
                tile = "rd00_"  # road, need to verify code
            row.append(tile)
        terrain.append(row)
    
    # Create objects
    new_objects = {}
    # Keep existing heroes and towns
    for k in ["hero_0", "hero_1", "town_0", "town_1"]:
        if k in objects:
            new_objects[k] = objects[k]
    
    # Set hero and town positions
    new_objects["hero_0"]["x"] = hx
    new_objects["hero_0"]["y"] = hy
    new_objects["town_0"]["x"] = max(0, hx - 2)
    new_objects["town_0"]["y"] = max(0, hy - 2)
    new_objects["hero_1"]["x"] = max(0, w - 5)
    new_objects["hero_1"]["y"] = max(0, h - 5)
    new_objects["town_1"]["x"] = max(0, w - 3)
    new_objects["town_1"]["y"] = max(0, h - 3)
    
    # Add mine
    new_objects["mine_0"] = {
        "l": 0,
        "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine",
        "x": mx,
        "y": my
    }
    
    # Add resource points
    for i, (rx, ry, rtype) in enumerate(resources):
        if rtype == 'gold':
            subtype = "core:resourceGold"
            template = {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]}
        elif rtype == 'wood':
            subtype = "core:resourceWood"
            template = {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]}
        elif rtype == 'rare':
            subtype = "core:resourceRare"
            template = {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]}
        elif rtype == 'chest':
            subtype = "core:chest"
            template = {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]}
        else:
            continue
        new_objects[f"resource_{i}"] = {
            "l": 0,
            "options": {},
            "subtype": subtype,
            "template": template,
            "type": "resource" if rtype != 'chest' else "chest",
            "x": rx,
            "y": ry
        }
    
    dst = os.path.join(dst_dir, f"{name}.vmap")
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, indent=2))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(new_objects, indent=2))
    
    print(f"Generated: {dst}")

print("Done")