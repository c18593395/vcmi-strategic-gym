import json, zipfile, os, random
from collections import deque

# 带路径验证的地图生成脚本
# 确保英雄到所有目标都有可通行路径

src = "D:/Bigdata/hero3_fresh/Maps/train_v1.vmap"
dst_dir = "D:/Bigdata/hero3_fresh/Maps/training"
os.makedirs(dst_dir, exist_ok=True)

def is_passable(code):
    return code in ('gr24_', 'rd00_')

def check_connectivity(terrain, w, h, start_x, start_y, targets):
    """检查起点到所有目标是否连通"""
    visited = set()
    queue = deque([(start_x, start_y)])
    visited.add((start_x, start_y))
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    while queue:
        x, y = queue.popleft()
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                if is_passable(terrain[ny][nx]):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    
    # 检查目标是否可达（目标格本身可以是不可通行的地形，但相邻格必须可达）
    results = []
    for name, tx, ty in targets:
        # 目标格本身
        if (tx, ty) in visited:
            results.append((name, True))
            continue
        # 检查目标相邻格
        reachable = False
        for dx, dy in directions:
            if (tx+dx, ty+dy) in visited:
                reachable = True
                break
        results.append((name, reachable))
    
    return results

def generate_terrain_with_paths(w, h, hx, hy, targets, obstacle_ratio=0.15):
    """生成地形，确保连通性"""
    max_attempts = 10
    
    for attempt in range(max_attempts):
        terrain = []
        for y in range(h):
            row = []
            for x in range(w):
                row.append("gr24_")
            terrain.append(row)
        
        # 添加障碍物（河流和岩石），但避开英雄和目标周围
        protected = set()
        protected.add((hx, hy))
        for _, tx, ty in targets:
            protected.add((tx, ty))
            # 保护目标周围
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    protected.add((tx+dx, ty+dy))
        
        # 添加河流（水平和垂直，但留出通道）
        num_rivers = random.randint(1, 3)
        for _ in range(num_rivers):
            if random.random() < 0.5:  # 水平河流
                y = random.randint(h//4, 3*h//4)
                gap_start = random.randint(0, w-4)
                gap_end = gap_start + random.randint(2, 4)
                for x in range(w):
                    if gap_start <= x <= gap_end:
                        continue  # 留出通道
                    if (x, y) not in protected:
                        terrain[y][x] = "wt00_"
            else:  # 垂直河流
                x = random.randint(w//4, 3*w//4)
                gap_start = random.randint(0, h-4)
                gap_end = gap_start + random.randint(2, 4)
                for y in range(h):
                    if gap_start <= y <= gap_end:
                        continue
                    if (x, y) not in protected:
                        terrain[y][x] = "wt00_"
        
        # 添加山脉（小集群，不形成屏障）
        num_mountains = random.randint(2, 5)
        for _ in range(num_mountains):
            mx = random.randint(3, w-4)
            my = random.randint(3, h-4)
            if (mx, my) in protected:
                continue
            # 小集群（2-3格）
            terrain[my][mx] = "ro00_"
            if random.random() < 0.5 and (mx+1, my) not in protected:
                terrain[my][mx+1] = "ro00_"
            if random.random() < 0.5 and (mx, my+1) not in protected:
                terrain[my+1][mx] = "ro00_"
        
        # 添加道路（从英雄到矿）
        mine_targets = [(n, tx, ty) for n, tx, ty in targets if 'mine' in n]
        if mine_targets:
            _, mtx, mty = mine_targets[0]
            # 简单L形道路
            x, y = hx, hy
            while x != mtx:
                terrain[y][x] = "rd00_"
                x += 1 if mtx > x else -1
            while y != mty:
                terrain[y][x] = "rd00_"
                y += 1 if mty > y else -1
            terrain[y][x] = "rd00_"
        
        # 验证连通性
        results = check_connectivity(terrain, w, h, hx, hy, targets)
        all_connected = all(r for _, r in results)
        
        if all_connected:
            return terrain
    
    # 如果多次尝试失败，返回全草地
    return [["gr24_"] * w for _ in range(h)]

# Level 1 地图定义
level1_maps = [
    ("T02_adventure_20X20_01", 20, 20, 2, 2, 15, 15, [(5,5,'gold'), (10,3,'wood'), (18,10,'rare')]),
    ("T02_adventure_20X20_02", 20, 20, 18, 18, 3, 3, [(5,15,'gold'), (15,5,'wood'), (10,10,'rare')]),
    ("T02_adventure_30X30_01", 30, 30, 3, 3, 25, 25, [(10,10,'gold'), (20,5,'wood'), (15,20,'rare')]),
    ("T02_adventure_30X30_02", 30, 30, 27, 27, 3, 3, [(5,25,'gold'), (25,5,'wood'), (15,15,'rare')]),
    ("T02_adventure_36X36_01", 36, 36, 3, 3, 30, 30, [(10,10,'gold'), (20,5,'wood'), (15,25,'rare')]),
    ("T02_adventure_36X36_02", 36, 36, 33, 33, 3, 3, [(5,30,'gold'), (30,5,'wood'), (18,18,'rare')]),
]

print("重新生成 Level 1 地图...")

for name, w, h, hx, hy, mx, my, resources in level1_maps:
    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        objects = json.loads(zin.read("objects.json"))
    
    header["name"] = name
    header["description"] = f"{w}x{h} terrain mix, multiple resources, training map"
    header["mapLevels"] = {"surface": {"height": h, "width": w, "index": 0}}
    
    # 准备目标列表
    targets = [("mine_0", mx, my)]
    for i, (rx, ry, _) in enumerate(resources):
        targets.append((f"resource_{i}", rx, ry))
    
    # 生成地形
    terrain = generate_terrain_with_paths(w, h, hx, hy, targets)
    
    # 创建对象
    new_objects = {}
    for k in ["hero_0", "hero_1", "town_0", "town_1"]:
        if k in objects:
            new_objects[k] = objects[k].copy()
    
    new_objects["hero_0"]["x"] = hx
    new_objects["hero_0"]["y"] = hy
    new_objects["town_0"]["x"] = max(0, hx - 2)
    new_objects["town_0"]["y"] = max(0, hy - 2)
    new_objects["hero_1"]["x"] = max(0, w - 5)
    new_objects["hero_1"]["y"] = max(0, h - 5)
    new_objects["town_1"]["x"] = max(0, w - 3)
    new_objects["town_1"]["y"] = max(0, h - 3)
    
    new_objects["mine_0"] = {
        "l": 0, "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine", "x": mx, "y": my
    }
    
    for i, (rx, ry, rtype) in enumerate(resources):
        subtype = f"core:resource{rtype.capitalize()}"
        new_objects[f"resource_{i}"] = {
            "l": 0, "options": {},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "resource", "x": rx, "y": ry
        }
    
    dst = os.path.join(dst_dir, f"{name}.vmap")
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, indent=2))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(new_objects, indent=2))
    
    # 验证连通性
    results = check_connectivity(terrain, w, h, hx, hy, targets)
    connected = sum(1 for _, r in results if r)
    print(f"  {name}: {connected}/{len(targets)} 可达")

print("Level 1 完成\n")

# Level 2 地图定义（类似结构，添加野怪）
level2_maps = [
    ("T03_adventure_20X20_01", 20, 20, 2, 2, 15, 15,
     [(5,5,'gold'), (10,3,'wood'), (18,10,'rare')],
     [(15,14,'core:peasant', 8, 'guard'), (5,4,'core:archer', 5, 'guard')]),
    ("T03_adventure_20X20_02", 20, 20, 18, 18, 3, 3,
     [(5,15,'gold'), (15,5,'wood'), (10,10,'rare')],
     [(3,4,'core:peasant', 6, 'guard'), (15,4,'core:archer', 4, 'guard')]),
    ("T03_adventure_30X30_01", 30, 30, 3, 3, 25, 25,
     [(10,10,'gold'), (20,5,'wood'), (15,20,'rare')],
     [(25,24,'core:peasant', 10, 'guard'), (10,9,'core:archer', 6, 'guard')]),
    ("T03_adventure_30X30_02", 30, 30, 27, 27, 3, 3,
     [(5,25,'gold'), (25,5,'wood'), (15,15,'rare')],
     [(3,4,'core:peasant', 8, 'guard'), (25,4,'core:archer', 5, 'guard')]),
    ("T03_adventure_36X36_01", 36, 36, 3, 3, 30, 30,
     [(10,10,'gold'), (20,5,'wood'), (15,25,'rare')],
     [(30,29,'core:peasant', 12, 'guard'), (10,9,'core:archer', 7, 'guard')]),
    ("T03_adventure_36X36_02", 36, 36, 33, 33, 3, 3,
     [(5,30,'gold'), (30,5,'wood'), (18,18,'rare')],
     [(3,4,'core:peasant', 10, 'guard'), (30,4,'core:archer', 6, 'guard')]),
]

print("重新生成 Level 2 地图...")

for name, w, h, hx, hy, mx, my, resources, monsters in level2_maps:
    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        objects = json.loads(zin.read("objects.json"))
    
    header["name"] = name
    header["description"] = f"{w}x{h} terrain mix, weak monsters, training map"
    header["mapLevels"] = {"surface": {"height": h, "width": w, "index": 0}}
    
    targets = [("mine_0", mx, my)]
    for i, (rx, ry, _) in enumerate(resources):
        targets.append((f"resource_{i}", rx, ry))
    
    terrain = generate_terrain_with_paths(w, h, hx, hy, targets)
    
    new_objects = {}
    for k in ["hero_0", "hero_1", "town_0", "town_1"]:
        if k in objects:
            new_objects[k] = objects[k].copy()
    
    new_objects["hero_0"]["x"] = hx
    new_objects["hero_0"]["y"] = hy
    new_objects["town_0"]["x"] = max(0, hx - 2)
    new_objects["town_0"]["y"] = max(0, hy - 2)
    new_objects["hero_1"]["x"] = max(0, w - 5)
    new_objects["hero_1"]["y"] = max(0, h - 5)
    new_objects["town_1"]["x"] = max(0, w - 3)
    new_objects["town_1"]["y"] = max(0, h - 3)
    
    new_objects["mine_0"] = {
        "l": 0, "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine", "x": mx, "y": my
    }
    
    for i, (rx, ry, rtype) in enumerate(resources):
        subtype = f"core:resource{rtype.capitalize()}"
        new_objects[f"resource_{i}"] = {
            "l": 0, "options": {},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "resource", "x": rx, "y": ry
        }
    
    for i, (mx_pos, my_pos, subtype, amount, aggression) in enumerate(monsters):
        new_objects[f"monster_{i}"] = {
            "l": 0, "options": {"amount": amount, "aggression": aggression, "formation": "wide"},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "monster", "x": mx_pos, "y": my_pos
        }
    
    dst = os.path.join(dst_dir, f"{name}.vmap")
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, indent=2))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(new_objects, indent=2))
    
    results = check_connectivity(terrain, w, h, hx, hy, targets)
    connected = sum(1 for _, r in results if r)
    print(f"  {name}: {connected}/{len(targets)} 可达")

print("Level 2 完成\n")

# Level 3 地图定义
level3_maps = [
    ("T04_adventure_20X20_01", 20, 20, 2, 2, 15, 15,
     [(5,5,'gold'), (10,3,'wood'), (18,10,'rare'), (12,18,'wood')],
     [(15,14,'core:peasant', 12, 'guard'), (5,4,'core:archer', 8, 'guard'), (18,9,'core:footman', 5, 'guard')]),
    ("T04_adventure_20X20_02", 20, 20, 18, 18, 3, 3,
     [(5,15,'gold'), (15,5,'wood'), (10,10,'rare'), (2,12,'wood')],
     [(3,4,'core:peasant', 10, 'guard'), (15,4,'core:archer', 6, 'guard'), (2,11,'core:footman', 4, 'guard')]),
    ("T04_adventure_30X30_01", 30, 30, 3, 3, 25, 25,
     [(10,10,'gold'), (20,5,'wood'), (15,20,'rare'), (25,15,'wood')],
     [(25,24,'core:peasant', 15, 'guard'), (10,9,'core:archer', 10, 'guard'), (25,14,'core:footman', 6, 'guard')]),
    ("T04_adventure_30X30_02", 30, 30, 27, 27, 3, 3,
     [(5,25,'gold'), (25,5,'wood'), (15,15,'rare'), (2,20,'wood')],
     [(3,4,'core:peasant', 12, 'guard'), (25,4,'core:archer', 8, 'guard'), (2,19,'core:footman', 5, 'guard')]),
    ("T04_adventure_36X36_01", 36, 36, 3, 3, 30, 30,
     [(10,10,'gold'), (20,5,'wood'), (15,25,'rare'), (30,15,'wood')],
     [(30,29,'core:peasant', 18, 'guard'), (10,9,'core:archer', 12, 'guard'), (30,14,'core:footman', 7, 'guard')]),
    ("T04_adventure_36X36_02", 36, 36, 33, 33, 3, 3,
     [(5,30,'gold'), (30,5,'wood'), (18,18,'rare'), (2,25,'wood')],
     [(3,4,'core:peasant', 15, 'guard'), (30,4,'core:archer', 10, 'guard'), (2,24,'core:footman', 6, 'guard')]),
]

print("重新生成 Level 3 地图...")

for name, w, h, hx, hy, mx, my, resources, monsters in level3_maps:
    with zipfile.ZipFile(src) as zin:
        header = json.loads(zin.read("header.json"))
        objects = json.loads(zin.read("objects.json"))
    
    header["name"] = name
    header["description"] = f"{w}x{h} terrain mix, town economy, training map"
    header["mapLevels"] = {"surface": {"height": h, "width": w, "index": 0}}
    
    targets = [("mine_0", mx, my)]
    for i, (rx, ry, _) in enumerate(resources):
        targets.append((f"resource_{i}", rx, ry))
    
    terrain = generate_terrain_with_paths(w, h, hx, hy, targets)
    
    new_objects = {}
    for k in ["hero_0", "hero_1", "town_0", "town_1"]:
        if k in objects:
            new_objects[k] = objects[k].copy()
    
    new_objects["hero_0"]["x"] = hx
    new_objects["hero_0"]["y"] = hy
    new_objects["town_0"]["x"] = max(0, hx - 2)
    new_objects["town_0"]["y"] = max(0, hy - 2)
    new_objects["hero_1"]["x"] = max(0, w - 5)
    new_objects["hero_1"]["y"] = max(0, h - 5)
    new_objects["town_1"]["x"] = max(0, w - 3)
    new_objects["town_1"]["y"] = max(0, h - 3)
    
    new_objects["mine_0"] = {
        "l": 0, "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine", "x": mx, "y": my
    }
    
    for i, (rx, ry, rtype) in enumerate(resources):
        subtype = f"core:resource{rtype.capitalize()}"
        new_objects[f"resource_{i}"] = {
            "l": 0, "options": {},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "resource", "x": rx, "y": ry
        }
    
    for i, (mx_pos, my_pos, subtype, amount, aggression) in enumerate(monsters):
        new_objects[f"monster_{i}"] = {
            "l": 0, "options": {"amount": amount, "aggression": aggression, "formation": "wide"},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "monster", "x": mx_pos, "y": my_pos
        }
    
    dst = os.path.join(dst_dir, f"{name}.vmap")
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, indent=2))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(new_objects, indent=2))
    
    results = check_connectivity(terrain, w, h, hx, hy, targets)
    connected = sum(1 for _, r in results if r)
    print(f"  {name}: {connected}/{len(targets)} 可达")

print("Level 3 完成")
print("\n所有地图重新生成完成！")