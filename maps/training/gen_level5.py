import json, zipfile, os, random

# Level 5 map generation script
# Complex battle, multiple towns and heroes

src = "D:/Bigdata/hero3_fresh/Maps/train_v1.vmap"
dst_dir = "D:/Bigdata/hero3_fresh/Maps/training"
os.makedirs(dst_dir, exist_ok=True)

# Level 5 map definitions
level5_maps = [
    ("T06_adventure_72X72_01", 72, 72),
    ("T06_adventure_72X72_02", 72, 72),
    ("T06_adventure_108X108_01", 108, 108),
    ("T06_adventure_108X108_02", 108, 108),
]

# Resource and monster templates
resource_types = ['gold', 'wood', 'rare']
weak_monsters = [('core:peasant', 20), ('core:archer', 15), ('core:footman', 10)]
medium_monsters = [('core:griffin', 8), ('core: pikeman', 12), ('core:cavalier', 5)]
strong_monsters = [('core:angel', 3), ('core:blackKnight', 4), ('core:hydra', 2)]

for name, w, h in level5_maps:
    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        terrain = json.loads(zin.read("surface_terrain.json"))
        objects = json.loads(zin.read("objects.json"))
    
    header["name"] = name
    header["description"] = f"{w}x{h} complex battle, multiple towns and heroes"
    header["mapLevels"] = {"surface": {"height": h, "width": w, "index": 0}}
    
    # Generate complex terrain
    terrain = []
    for y in range(h):
        row = []
        for x in range(w):
            tile = "gr24_"
            # Rivers (multiple horizontal and vertical)
            if (y == h//4 and x > w//8 and x < 7*w//8) or \
               (y == 3*h//4 and x > w//8 and x < 7*w//8):
                tile = "wt00_"
            if (x == w//4 and y > h//8 and y < 7*h//8) or \
               (x == 3*w//4 and y > h//8 and y < 7*h//8):
                tile = "wt00_"
            # Mountain ranges
            if (x > 10 and x < 20 and y > 10 and y < 20) or \
               (x > w-21 and x < w-11 and y > h-21 and y < h-11):
                if random.random() < 0.4:
                    tile = "ro00_"
            # Sand patches
            if (x > w//3 and x < 2*w//3 and y > h//3 and y < 2*h//3):
                if random.random() < 0.2:
                    tile = "sa00_"
            # Roads (main paths)
            if x == w//2 or y == h//2 or abs(x-y) < 3 or abs(x-(w-y)) < 3:
                tile = "rd00_"
            row.append(tile)
        terrain.append(row)
    
    new_objects = {}
    
    # Player (red) - bottom left
    new_objects["hero_0"] = objects["hero_0"].copy()
    new_objects["hero_0"]["x"] = 5
    new_objects["hero_0"]["y"] = 5
    new_objects["hero_0"]["options"]["owner"] = "red"
    
    new_objects["town_0"] = objects["town_0"].copy()
    new_objects["town_0"]["x"] = 2
    new_objects["town_0"]["y"] = 2
    new_objects["town_0"]["options"]["owner"] = "red"
    
    # AI players (blue) - spread around map
    ai_positions = [
        (w-6, h-6), (w-6, 5), (5, h-6),
        (w//2, 5), (w//2, h-6), (5, h//2), (w-6, h//2)
    ]
    ai_town_positions = [
        (w-3, h-3), (w-3, 2), (2, h-3),
        (w//2, 2), (w//2, h-3), (2, h//2), (w-3, h//2)
    ]
    
    for i, (hx, hy) in enumerate(ai_positions[:3]):  # Only 3 AI for now
        new_objects[f"hero_{i+1}"] = objects["hero_1"].copy()
        new_objects[f"hero_{i+1}"]["x"] = hx
        new_objects[f"hero_{i+1}"]["y"] = hy
        new_objects[f"hero_{i+1}"]["options"]["owner"] = "blue"
    
    for i, (tx, ty) in enumerate(ai_town_positions[:3]):
        new_objects[f"town_{i+1}"] = objects["town_1"].copy()
        new_objects[f"town_{i+1}"]["x"] = tx
        new_objects[f"town_{i+1}"]["y"] = ty
        new_objects[f"town_{i+1}"]["options"]["owner"] = "blue"
    
    # Add mines (distributed)
    mine_positions = [
        (w//4, h//4), (3*w//4, 3*h//4), (w//4, 3*h//4), (3*w//4, h//4),
        (w//2, h//2), (w//3, h//3), (2*w//3, 2*h//3)
    ]
    for i, (mx, my) in enumerate(mine_positions[:5]):
        new_objects[f"mine_{i}"] = {
            "l": 0, "options": {"owner": None},
            "subtype": "core:goldMine",
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "mine", "x": mx, "y": my
        }
    
    # Add resource points (many)
    resource_positions = []
    for _ in range(15):
        rx = random.randint(5, w-6)
        ry = random.randint(5, h-6)
        rtype = random.choice(resource_types)
        resource_positions.append((rx, ry, rtype))
    
    for i, (rx, ry, rtype) in enumerate(resource_positions):
        if rtype == 'gold':
            subtype = "core:resourceGold"
        elif rtype == 'wood':
            subtype = "core:resourceWood"
        else:
            subtype = "core:resourceRare"
        new_objects[f"resource_{i}"] = {
            "l": 0, "options": {},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "resource", "x": rx, "y": ry
        }
    
    # Add monsters (various strengths)
    monster_positions = []
    for _ in range(20):
        mx = random.randint(5, w-6)
        my = random.randint(5, h-6)
        monster_positions.append((mx, my))
    
    for i, (mx, my) in enumerate(monster_positions):
        if i < 8:
            subtype, amount = weak_monsters[i % 3]
        elif i < 15:
            subtype, amount = medium_monsters[(i-8) % 3]
        else:
            subtype, amount = strong_monsters[(i-15) % 3]
        new_objects[f"monster_{i}"] = {
            "l": 0, "options": {"amount": amount, "aggression": "guard", "formation": "wide"},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "monster", "x": mx, "y": my
        }
    
    dst = os.path.join(dst_dir, f"{name}.vmap")
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, indent=2))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(new_objects, indent=2))
    
    print(f"Generated: {dst}")

print("Done")