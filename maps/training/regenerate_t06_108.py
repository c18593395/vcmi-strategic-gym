import json, zipfile, os, random
from collections import deque

# 重新生成 T06_adventure_108X108_02

src = "D:/Bigdata/hero3_fresh/Maps/train_v1.vmap"
dst_dir = "D:/Bigdata/hero3_fresh/Maps/training"

def is_passable(code):
    return code in ('gr24_', 'rd00_')

def check_connectivity(terrain, w, h, start_x, start_y, targets):
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
    for attempt in range(30):
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
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    protected.add((tx+dx, ty+dy))
        
        # 添加河流（留出通道）
        for i in range(3):
            y = random.randint(h//5, 4*h//5)
            gap_start = random.randint(0, w-8)
            gap_end = gap_start + random.randint(4, 7)
            for x in range(w):
                if gap_start <= x <= gap_end:
                    continue
                if (x, y) not in protected:
                    terrain[y][x] = "wt00_"
        
        for i in range(3):
            x = random.randint(w//5, 4*w//5)
            gap_start = random.randint(0, h-8)
            gap_end = gap_start + random.randint(4, 7)
            for y in range(h):
                if gap_start <= y <= gap_end:
                    continue
                if (x, y) not in protected:
                    terrain[y][x] = "wt00_"
        
        # 添加山脉
        for _ in range(12):
            mx = random.randint(8, w-9)
            my = random.randint(8, h-9)
            if (mx, my) in protected:
                continue
            terrain[my][mx] = "ro00_"
            if random.random() < 0.4 and (mx+1, my) not in protected:
                terrain[my][mx+1] = "ro00_"
            if random.random() < 0.4 and (mx, my+1) not in protected:
                terrain[my+1][mx] = "ro00_"
        
        # 添加沙地
        for _ in range(15):
            sx = random.randint(8, w-9)
            sy = random.randint(8, h-9)
            if (sx, sy) in protected:
                continue
            if random.random() < 0.3:
                terrain[sy][sx] = "sa00_"
        
        # 添加主干道路
        road_y = h // 2
        for x in range(w):
            terrain[road_y][x] = "rd00_"
        
        road_x = w // 2
        for y in range(h):
            terrain[y][road_x] = "rd00_"
        
        # 从英雄位置到各个矿添加道路
        mine_targets = [(n, tx, ty) for n, tx, ty in targets if 'mine' in n]
        for _, mtx, mty in mine_targets[:3]:
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
    
    return None, 30

# 地图参数
name = "T06_adventure_108X108_02"
w, h = 108, 108
hx, hy = 5, 5

# 读取模板
with zipfile.ZipFile(src) as zin:
    objects = json.loads(zin.read("objects.json"))

# 固定矿位置
mine_positions = [
    (w//4, h//4), (3*w//4, 3*h//4), (w//4, 3*h//4), (3*w//4, h//4),
    (w//2, h//2)
]

# 生成目标列表
targets = [(f"mine_{i}", mx, my) for i, (mx, my) in enumerate(mine_positions)]

print(f"重新生成: {name}")

# 生成地形
terrain, attempts = generate_terrain(w, h, hx, hy, targets)

if terrain is None:
    print("❌ 无法生成连通地形")
    exit(1)

print(f"  地形生成: {attempts} 次尝试")

# 保护区域
protected = set()
protected.add((hx, hy))
for _, tx, ty in targets:
    protected.add((tx, ty))
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            protected.add((tx+dx, ty+dy))

# 生成资源点位置（确保在可通行地形上）
resource_positions = []
resource_types = ['gold', 'wood', 'rare']

for i in range(15):
    for attempt in range(100):
        rx = random.randint(10, w-11)
        ry = random.randint(10, h-11)
        if (rx, ry) not in protected and is_passable(terrain[ry][rx]):
            resource_positions.append((rx, ry))
            break

# 创建 header
header = {
    "name": name,
    "description": f"{w}x{h} complex battle, multiple towns and heroes",
    "mapLevels": {"surface": {"height": h, "width": w, "index": 0}},
    "mods": [],
    "players": []
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
weak_monsters = [('core:peasant', 20), ('core:archer', 15), ('core:footman', 10)]
medium_monsters = [('core:griffin', 8), ('core:pikeman', 12), ('core:cavalier', 5)]
strong_monsters = [('core:angel', 3), ('core:blackKnight', 4), ('core:hydra', 2)]

monster_positions = []
for _ in range(20):
    for attempt in range(50):
        mmx = random.randint(10, w-11)
        mmy = random.randint(10, h-11)
        if (mmx, mmy) not in protected and is_passable(terrain[mmy][mmx]):
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
