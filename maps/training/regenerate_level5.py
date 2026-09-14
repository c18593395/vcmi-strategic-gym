import json, zipfile, os, random
from collections import deque

# Level 5 地图重新生成脚本
# 只重新生成有问题的两个地图

src = "D:/Bigdata/hero3_fresh/Maps/train_v1.vmap"
dst_dir = "D:/Bigdata/hero3_fresh/Maps/training"

def is_passable(code):
    """检查地形是否可通行"""
    return code in ('gr24_', 'rd00_')

def check_connectivity(terrain, w, h, start_x, start_y, targets):
    """BFS检查连通性"""
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
    
    results = []
    for name, tx, ty in targets:
        if (tx, ty) in visited:
            results.append((name, True))
            continue
        reachable = False
        for dx, dy in directions:
            if (tx+dx, ty+dy) in visited:
                reachable = True
                break
        results.append((name, reachable))
    
    return results

def generate_terrain(w, h, hx, hy, targets):
    """生成地形，确保连通性"""
    for attempt in range(20):
        terrain = []
        for y in range(h):
            row = []
            for x in range(w):
                row.append("gr24_")
            terrain.append(row)
        
        # 保护区域
        protected = set()
        protected.add((hx, hy))
        for _, tx, ty in targets:
            protected.add((tx, ty))
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    protected.add((tx+dx, ty+dy))
        
        # 添加河流（留出通道）
        # 水平河流
        for i in range(2):
            y = random.randint(h//5, 4*h//5)
            gap_start = random.randint(0, w-6)
            gap_end = gap_start + random.randint(3, 5)
            for x in range(w):
                if gap_start <= x <= gap_end:
                    continue
                if (x, y) not in protected:
                    terrain[y][x] = "wt00_"
        
        # 垂直河流
        for i in range(2):
            x = random.randint(w//5, 4*w//5)
            gap_start = random.randint(0, h-6)
            gap_end = gap_start + random.randint(3, 5)
            for y in range(h):
                if gap_start <= y <= gap_end:
                    continue
                if (x, y) not in protected:
                    terrain[y][x] = "wt00_"
        
        # 添加山脉（小集群，避开保护区域）
        for _ in range(8):
            mx = random.randint(5, w-6)
            my = random.randint(5, h-6)
            if (mx, my) in protected:
                continue
            terrain[my][mx] = "ro00_"
            if random.random() < 0.4 and (mx+1, my) not in protected:
                terrain[my][mx+1] = "ro00_"
            if random.random() < 0.4 and (mx, my+1) not in protected:
                terrain[my+1][mx] = "ro00_"
        
        # 添加沙地
        for _ in range(10):
            sx = random.randint(5, w-6)
            sy = random.randint(5, h-6)
            if (sx, sy) in protected:
                continue
            if random.random() < 0.3:
                terrain[sy][sx] = "sa00_"
        
        # 添加主干道路
        # 水平主干道
        road_y = h // 2
        for x in range(w):
            if (x, road_y) not in protected or terrain[road_y][x] == "wt00_":
                terrain[road_y][x] = "rd00_"
        
        # 垂直主干道
        road_x = w // 2
        for y in range(h):
            if (road_x, y) not in protected or terrain[y][road_x] == "wt00_":
                terrain[y][road_x] = "rd00_"
        
        # 从英雄位置到各个矿添加道路
        mine_targets = [(n, tx, ty) for n, tx, ty in targets if 'mine' in n]
        for _, mtx, mty in mine_targets[:2]:
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
            return terrain, attempt+1
    
    return None, 20

def generate_resource_positions(w, h, num_resources, protected):
    """生成资源点位置，确保在可通行地形上"""
    positions = []
    max_attempts = 100
    
    for _ in range(num_resources):
        for attempt in range(max_attempts):
            rx = random.randint(8, w-9)
            ry = random.randint(8, h-9)
            if (rx, ry) not in protected:
                positions.append((rx, ry))
                break
    
    return positions

# 重新生成的地图定义
maps_to_regenerate = [
    ("T06_adventure_72X72_02", 72, 72),
    ("T06_adventure_108X108_02", 108, 108),
]

resource_types = ['gold', 'wood', 'rare']
weak_monsters = [('core:peasant', 20), ('core:archer', 15), ('core:footman', 10)]
medium_monsters = [('core:griffin', 8), ('core:pikeman', 12), ('core:cavalier', 5)]
strong_monsters = [('core:angel', 3), ('core:blackKnight', 4), ('core:hydra', 2)]

print("重新生成 Level 5 问题地图...")

for name, w, h in maps_to_regenerate:
    print(f"\n生成: {name} ({w}x{h})")
    
    with zipfile.ZipFile(src) as zin:
        objects = json.loads(zin.read("objects.json"))
    
    # 固定位置
    hx, hy = 5, 5
    mine_positions = [
        (w//4, h//4), (3*w//4, 3*h//4), (w//4, 3*h//4), (3*w//4, h//4),
        (w//2, h//2)
    ]
    
    # 生成目标列表
    targets = []
    for i, (mx, my) in enumerate(mine_positions):
        targets.append((f"mine_{i}", mx, my))
    
    # 生成地形
    terrain, attempts = generate_terrain(w, h, hx, hy, targets)
    
    if terrain is None:
        print(f"  ❌ 无法生成连通地形，跳过")
        continue
    
    print(f"  地形生成: {attempts} 次尝试")
    
    # 保护区域
    protected = set()
    protected.add((hx, hy))
    for _, tx, ty in targets:
        protected.add((tx, ty))
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                protected.add((tx+dx, ty+dy))
    
    # 生成资源点位置
    resource_positions = generate_resource_positions(w, h, 15, protected)
    
    # 创建 header
    # 09-14 治本: 补引擎启动必需的 8 字段 — 缺 victoryConditions 等会导致
    # "Failed to launch game: Invalid range provided: 0 ... -1" (72系挂死/108系SIGSEGV)
    # players 仍由 patch_t06_02_players.py 注入, 入池前必扫 py/_scan_players.py
    header = {
        "allowedArtifacts": {"anyOf": ["core:pendantOfFreeWill"]},
        "defeatIconIndex": 3,
        "name": name,
        "description": f"{w}x{h} complex battle, multiple towns and heroes",
        "difficulty": "NORMAL",
        "mapLevels": {"surface": {"height": h, "width": w, "index": 0}},
        "mods": None,
        "players": [],
        "victoryConditions": ["standardDefeat", "specialVictory"],
        "triggeredEvents": {
            "specialVictory": {
                "condition": ["allOf", ["isHuman", {"value": 1}],
                              ["haveResources", {"type": 0, "value": 100}]],
                "effect": {"type": "victory"},
                "message": {"exactStrings": None, "localStrings": None,
                            "message": [2], "numbers": None,
                            "stringsTextID": ["core.genrltxt.278"]},
            },
            "standardDefeat": {
                "condition": ["daysWithoutTown", {"value": 7}],
                "effect": {"type": "defeat"},
                "message": {"exactStrings": None, "localStrings": None,
                            "message": [2], "numbers": None,
                            "stringsTextID": ["core.genrltxt.7"]},
            },
        },
        "versionMajor": 1,
        "versionMinor": 1,
        "victoryIconIndex": 2,
    }
    
    # 创建对象
    new_objects = {}
    
    # Player (red)
    new_objects["hero_0"] = objects["hero_0"].copy()
    new_objects["hero_0"]["x"] = hx
    new_objects["hero_0"]["y"] = hy
    new_objects["hero_0"]["options"]["owner"] = "red"
    
    new_objects["town_0"] = objects["town_0"].copy()
    new_objects["town_0"]["x"] = 2
    new_objects["town_0"]["y"] = 2
    new_objects["town_0"]["options"]["owner"] = "red"
    
    # AI players (blue)
    ai_positions = [(w-6, h-6), (w-6, 5), (5, h-6)]
    ai_town_positions = [(w-3, h-3), (w-3, 2), (2, h-3)]
    
    for i, (ahx, ahy) in enumerate(ai_positions):
        new_objects[f"hero_{i+1}"] = objects["hero_1"].copy()
        new_objects[f"hero_{i+1}"]["x"] = ahx
        new_objects[f"hero_{i+1}"]["y"] = ahy
        new_objects[f"hero_{i+1}"]["options"]["owner"] = "blue"
    
    for i, (atx, aty) in enumerate(ai_town_positions):
        new_objects[f"town_{i+1}"] = objects["town_1"].copy()
        new_objects[f"town_{i+1}"]["x"] = atx
        new_objects[f"town_{i+1}"]["y"] = aty
        new_objects[f"town_{i+1}"]["options"]["owner"] = "blue"
    
    # 添加矿
    for i, (mx, my) in enumerate(mine_positions):
        new_objects[f"mine_{i}"] = {
            "l": 0, "options": {"owner": None},
            "subtype": "core:goldMine",
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "mine", "x": mx, "y": my
        }
    
    # 添加资源点
    for i, (rx, ry) in enumerate(resource_positions):
        rtype = resource_types[i % 3]
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
    
    # 添加野怪
    monster_positions = []
    for _ in range(20):
        for attempt in range(50):
            mmx = random.randint(8, w-9)
            mmy = random.randint(8, h-9)
            if (mmx, mmy) not in protected:
                monster_positions.append((mmx, mmy))
                break
    
    for i, (mmx, mmy) in enumerate(monster_positions):
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
            "type": "monster", "x": mmx, "y": mmy
        }
    
    # 保存
    dst = os.path.join(dst_dir, f"{name}.vmap")
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, indent=2))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(new_objects, indent=2))
    
    # 验证连通性
    all_targets = [(f"mine_{i}", mx, my) for i, (mx, my) in enumerate(mine_positions)]
    all_targets += [(f"resource_{i}", rx, ry) for i, (rx, ry) in enumerate(resource_positions)]
    
    results = check_connectivity(terrain, w, h, hx, hy, all_targets)
    reachable = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"  ✅ 生成完成: {dst}")
    print(f"  BFS验证: {reachable}/{total} 可达 ({100*reachable/total:.1f}%)")

print("\n重新生成完成！")