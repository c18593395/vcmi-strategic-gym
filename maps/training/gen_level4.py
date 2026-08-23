import json, zipfile, os, random

# Level 4 map generation script
# 1v1 simple AI, symmetric layout

src = "D:/Bigdata/hero3_fresh/Maps/train_v1.vmap"
dst_dir = "D:/Bigdata/hero3_fresh/Maps/training"
os.makedirs(dst_dir, exist_ok=True)

# Level 4 map definitions: (name, w, h, resources, monsters)
level4_maps = [
    ("T05_adventure_36X36_01", 36, 36,
     [(18,18,'gold'), (10,10,'wood'), (26,26,'rare'), (18,5,'wood'), (5,18,'gold')],
     [(18,17,'core:peasant', 15, 'guard'), (17,18,'core:archer', 10, 'guard'),
      (10,9,'core:footman', 8, 'guard'), (26,25,'core:footman', 8, 'guard')]),
    ("T05_adventure_36X36_02", 36, 36,
     [(18,18,'gold'), (8,8,'wood'), (28,28,'rare'), (18,30,'wood'), (30,18,'gold')],
     [(18,17,'core:peasant', 15, 'guard'), (17,18,'core:archer', 10, 'guard'),
      (8,7,'core:footman', 8, 'guard'), (28,27,'core:footman', 8, 'guard')]),
    ("T05_adventure_52X52_01", 52, 52,
     [(26,26,'gold'), (15,15,'wood'), (37,37,'rare'), (26,10,'wood'), (10,26,'gold')],
     [(26,25,'core:peasant', 20, 'guard'), (25,26,'core:archer', 15, 'guard'),
      (15,14,'core:footman', 10, 'guard'), (37,36,'core:footman', 10, 'guard')]),
    ("T05_adventure_52X52_02", 52, 52,
     [(26,26,'gold'), (12,12,'wood'), (40,40,'rare'), (26,42,'wood'), (42,26,'gold')],
     [(26,25,'core:peasant', 20, 'guard'), (25,26,'core:archer', 15, 'guard'),
      (12,11,'core:footman', 10, 'guard'), (40,39,'core:footman', 10, 'guard')]),
]

for name, w, h, resources, monsters in level4_maps:
    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        terrain = json.loads(zin.read("surface_terrain.json"))
        objects = json.loads(zin.read("objects.json"))
    
    header["name"] = name
    header["description"] = f"{w}x{h} 1v1 simple AI, symmetric layout"
    header["mapLevels"] = {"surface": {"height": h, "width": w, "index": 0}}
    
    # Generate terrain
    terrain = []
    for y in range(h):
        row = []
        for x in range(w):
            tile = "gr24_"
            # Central river barrier
            if y == h//2 and abs(x - w//2) > 3:
                tile = "wt00_"
            # Mountain clusters
            if (x < 8 and y < 8) or (x > w-9 and y > h-9):
                if random.random() < 0.3:
                    tile = "ro00_"
            # Main roads (diagonal and center)
            if abs(x - y) < 2 or (x == w//2) or (y == h//2):
                tile = "rd00_"
            row.append(tile)
        terrain.append(row)
    
    # Create objects - symmetric layout
    new_objects = {}
    
    # Red player (bottom-left)
    new_objects["hero_0"] = objects["hero_0"].copy()
    new_objects["hero_0"]["x"] = 3
    new_objects["hero_0"]["y"] = 3
    new_objects["hero_0"]["options"]["owner"] = "red"
    
    new_objects["town_0"] = objects["town_0"].copy()
    new_objects["town_0"]["x"] = 1
    new_objects["town_0"]["y"] = 1
    new_objects["town_0"]["options"]["owner"] = "red"
    
    # Blue player (top-right)
    new_objects["hero_1"] = objects["hero_1"].copy()
    new_objects["hero_1"]["x"] = w - 4
    new_objects["hero_1"]["y"] = h - 4
    new_objects["hero_1"]["options"]["owner"] = "blue"
    
    new_objects["town_1"] = objects["town_1"].copy()
    new_objects["town_1"]["x"] = w - 2
    new_objects["town_1"]["y"] = h - 2
    new_objects["town_1"]["options"]["owner"] = "blue"
    
    # Add mines (neutral, in contested area)
    new_objects["mine_0"] = {
        "l": 0, "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine", "x": w//3, "y": h//3
    }
    new_objects["mine_1"] = {
        "l": 0, "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine", "x": 2*w//3, "y": 2*h//3
    }
    
    # Add resource points
    for i, (rx, ry, rtype) in enumerate(resources):
        if rtype == 'gold':
            subtype = "core:resourceGold"
        elif rtype == 'wood':
            subtype = "core:resourceWood"
        elif rtype == 'rare':
            subtype = "core:resourceRare"
        else:
            continue
        new_objects[f"resource_{i}"] = {
            "l": 0, "options": {},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "resource", "x": rx, "y": ry
        }
    
    # Add monsters
    for i, (mx, my, subtype, amount, aggression) in enumerate(monsters):
        new_objects[f"monster_{i}"] = {
            "l": 0, "options": {"amount": amount, "aggression": aggression, "formation": "wide"},
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