import json, zipfile, os

src = "/mnt/d/Bigdata/hero3_fresh/Maps/train_v1.vmap"
dst_dir = "/mnt/d/Bigdata/hero3_fresh/Maps/training"
os.makedirs(dst_dir, exist_ok=True)

maps = [
    ("T01_adventure_20X20_01", 20, 20, 9, 8, 8, 8, 15, 15),
    ("T01_adventure_20X20_02", 20, 20, 2, 2, 1, 2, 18, 18),
    ("T01_adventure_30X30_01", 30, 30, 5, 15, 3, 15, 25, 15),
    ("T01_adventure_30X30_02", 30, 30, 2, 2, 1, 2, 28, 28),
    ("T01_adventure_36X36_01", 36, 36, 5, 18, 3, 18, 30, 18),
]

for name, w, h, hx, hy, tx, ty, mx, my in maps:
    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        terrain = json.loads(zin.read("surface_terrain.json"))
        objects = json.loads(zin.read("objects.json"))

    header["name"] = name
    header["description"] = f"{w}x{h} no obstacles, training map"
    header["mapLevels"] = {"surface": {"height": h, "width": w, "index": 0}}
    header["players"] = [{"canComputerPlay": True, "canHumanPlay": True, "mainHero": None}]

    terrain = [["gr24_"] * w for _ in range(h)]

    new_objects = {}
    for k in ["hero_0", "town_0"]:
        if k in objects:
            new_objects[k] = objects[k]

    new_objects["mine_0"] = {
        "l": 0, "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine", "x": mx, "y": my
    }

    # 确保不超出边界 (模板至少 4 格)
    hx = max(4, min(w-5, hx))
    hy = max(4, min(h-5, hy))
    mx = max(4, min(w-5, mx))
    my = max(4, min(h-5, my))
    tx = max(4, min(w-5, tx))
    ty = max(4, min(h-5, ty))
    new_objects["hero_0"]["x"] = hx
    new_objects["hero_0"]["y"] = hy
    new_objects["town_0"]["x"] = tx
    new_objects["town_0"]["y"] = ty

    dst = os.path.join(dst_dir, f"{name}.vmap")
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, indent=2))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(new_objects, indent=2))

    print(f"Generated: {dst}")

print("Done")
