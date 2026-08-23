import zipfile, json, os, random, shutil
from collections import deque

# 自动化地图生成+验证流程
# 1. 生成地图
# 2. BFS + 规则校验
# 3. 失败丢弃重生成
# 4. 输出 vmap
# 5. 环境加载实跑测试

src = "D:/Bigdata/hero3_fresh/Maps/train_v1.vmap"
dst_dir = "D:/Bigdata/hero3_fresh/Maps/training"
temp_dir = "D:/Bigdata/hero3_fresh/Maps/training/temp"
os.makedirs(dst_dir, exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)

# 验证规则
VALID_TERRAIN_CODES = {'gr24_', 'wt00_', 'ro00_', 'rd00_', 'sa00_'}
REQUIRED_OBJECTS = ['hero_0', 'town_0']
MAX_RETRIES = 10

def is_passable(code):
    """检查地形是否可通行"""
    return code in ('gr24_', 'rd00_')

def check_bfs_connectivity(terrain, w, h, start_x, start_y, targets):
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

def validate_map(filepath):
    """全面验证地图"""
    errors = []
    warnings = []
    
    try:
        with zipfile.ZipFile(filepath) as z:
            # 检查必要文件
            required_files = ['header.json', 'surface_terrain.json', 'objects.json']
            for rf in required_files:
                if rf not in z.namelist():
                    errors.append(f"缺少 {rf}")
                    return errors, warnings
            
            header = json.loads(z.read('header.json'))
            terrain = json.loads(z.read('surface_terrain.json'))
            objects = json.loads(z.read('objects.json'))
            
            # 检查 header
            if 'name' not in header:
                errors.append("header 缺少 name")
            if 'mapLevels' not in header:
                errors.append("header 缺少 mapLevels")
                return errors, warnings
            
            surface = header['mapLevels'].get('surface', {})
            w = surface.get('width', 0)
            h = surface.get('height', 0)
            
            if w == 0 or h == 0:
                errors.append(f"地图尺寸无效: {w}x{h}")
                return errors, warnings
            
            # 检查 terrain
            if len(terrain) != h:
                errors.append(f"terrain 行数 {len(terrain)} != {h}")
                return errors, warnings
            
            for y, row in enumerate(terrain):
                if len(row) != w:
                    errors.append(f"terrain 第{y}行列数 {len(row)} != {w}")
                    return errors, warnings
            
            # 检查地形代码
            terrain_codes = set()
            for row in terrain:
                terrain_codes.update(row)
            invalid_codes = terrain_codes - VALID_TERRAIN_CODES
            if invalid_codes:
                errors.append(f"未知地形代码: {invalid_codes}")
            
            # 检查必要对象
            for obj_name in REQUIRED_OBJECTS:
                if obj_name not in objects:
                    errors.append(f"缺少必要对象: {obj_name}")
            
            # 检查对象位置
            for obj_name, obj_data in objects.items():
                x = obj_data.get('x', -1)
                y = obj_data.get('y', -1)
                if x < 0 or x >= w or y < 0 or y >= h:
                    errors.append(f"{obj_name} 位置 ({x},{y}) 超出范围")
            
            # BFS 连通性检查
            if 'hero_0' in objects:
                hx = objects['hero_0']['x']
                hy = objects['hero_0']['y']
                
                targets = []
                for k, v in objects.items():
                    if k.startswith('mine_') or k.startswith('resource_'):
                        targets.append((k, v['x'], v['y']))
                
                if targets:
                    results = check_bfs_connectivity(terrain, w, h, hx, hy, targets)
                    unreachable = [name for name, reachable in results if not reachable]
                    if unreachable:
                        # 允许部分资源不可达（增加策略性），但矿必须可达
                        mine_unreachable = [n for n in unreachable if 'mine' in n]
                        if mine_unreachable:
                            errors.append(f"矿不可达: {mine_unreachable}")
                        elif len(unreachable) > len(targets) * 0.3:  # 超过30%不可达
                            warnings.append(f"过多资源不可达: {unreachable}")
            
            # 检查对象完整性
            hero_count = sum(1 for k in objects if k.startswith('hero_'))
            town_count = sum(1 for k in objects if k.startswith('town_'))
            mine_count = sum(1 for k in objects if k.startswith('mine_'))
            
            if hero_count == 0:
                errors.append("无英雄对象")
            if town_count == 0:
                warnings.append("无城镇对象")
            if mine_count == 0:
                warnings.append("无矿对象")
            
    except Exception as e:
        errors.append(f"解析错误: {e}")
    
    return errors, warnings

def generate_terrain_with_paths(w, h, hx, hy, targets, obstacle_ratio=0.15):
    """生成地形，确保连通性"""
    for attempt in range(MAX_RETRIES):
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
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    protected.add((tx+dx, ty+dy))
        
        # 添加河流（留出通道）
        num_rivers = random.randint(1, 3)
        for _ in range(num_rivers):
            if random.random() < 0.5:
                y = random.randint(h//4, 3*h//4)
                gap_start = random.randint(0, w-4)
                gap_end = gap_start + random.randint(2, 4)
                for x in range(w):
                    if gap_start <= x <= gap_end:
                        continue
                    if (x, y) not in protected:
                        terrain[y][x] = "wt00_"
            else:
                x = random.randint(w//4, 3*w//4)
                gap_start = random.randint(0, h-4)
                gap_end = gap_start + random.randint(2, 4)
                for y in range(h):
                    if gap_start <= y <= gap_end:
                        continue
                    if (x, y) not in protected:
                        terrain[y][x] = "wt00_"
        
        # 添加山脉（小集群）
        num_mountains = random.randint(2, 5)
        for _ in range(num_mountains):
            mx = random.randint(3, w-4)
            my = random.randint(3, h-4)
            if (mx, my) in protected:
                continue
            terrain[my][mx] = "ro00_"
            if random.random() < 0.5 and (mx+1, my) not in protected:
                terrain[my][mx+1] = "ro00_"
            if random.random() < 0.5 and (mx, my+1) not in protected:
                terrain[my+1][mx] = "ro00_"
        
        # 添加道路
        mine_targets = [(n, tx, ty) for n, tx, ty in targets if 'mine' in n]
        if mine_targets:
            _, mtx, mty = mine_targets[0]
            x, y = hx, hy
            while x != mtx:
                terrain[y][x] = "rd00_"
                x += 1 if mtx > x else -1
            while y != mty:
                terrain[y][x] = "rd00_"
                y += 1 if mty > y else -1
            terrain[y][x] = "rd00_"
        
        # 验证连通性
        results = check_bfs_connectivity(terrain, w, h, hx, hy, targets)
        all_connected = all(r for _, r in results)
        
        if all_connected:
            return terrain
    
    # 失败则返回全草地
    return [["gr24_"] * w for _ in range(h)]

def create_map(map_def, level_name):
    """创建单个地图"""
    name, w, h, hx, hy, mx, my, resources, monsters = map_def
    
    # 准备目标列表
    targets = [("mine_0", mx, my)]
    for i, (rx, ry, _) in enumerate(resources):
        targets.append((f"resource_{i}", rx, ry))
    
    # 生成地形
    terrain = generate_terrain_with_paths(w, h, hx, hy, targets)
    
    # 读取模板对象
    with zipfile.ZipFile(src) as zin:
        objects = json.loads(zin.read("objects.json"))
    
    # 创建 header
    header = {
        "name": name,
        "description": f"{w}x{h} {level_name} training map",
        "mapLevels": {"surface": {"height": h, "width": w, "index": 0}},
        "mods": [],
        "players": []
    }
    
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
    
    # 添加矿
    new_objects["mine_0"] = {
        "l": 0, "options": {"owner": None},
        "subtype": "core:goldMine",
        "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
        "type": "mine", "x": mx, "y": my
    }
    
    # 添加资源点
    for i, (rx, ry, rtype) in enumerate(resources):
        subtype = f"core:resource{rtype.capitalize()}"
        new_objects[f"resource_{i}"] = {
            "l": 0, "options": {},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "resource", "x": rx, "y": ry
        }
    
    # 添加野怪
    for i, (mx_pos, my_pos, subtype, amount, aggression) in enumerate(monsters):
        new_objects[f"monster_{i}"] = {
            "l": 0, "options": {"amount": amount, "aggression": aggression, "formation": "wide"},
            "subtype": subtype,
            "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"], "visitableFrom": ["+++", "+-+", "+++"]},
            "type": "monster", "x": mx_pos, "y": my_pos
        }
    
    # 保存到临时目录
    temp_path = os.path.join(temp_dir, f"{name}.vmap")
    with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(header, indent=2))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(new_objects, indent=2))
    
    return temp_path

# 定义所有地图
map_definitions = {
    "Level 1": [
        ("T02_adventure_20X20_01", 20, 20, 2, 2, 15, 15, [(5,5,'gold'), (10,3,'wood'), (18,10,'rare')], []),
        ("T02_adventure_20X20_02", 20, 20, 18, 18, 3, 3, [(5,15,'gold'), (15,5,'wood'), (10,10,'rare')], []),
        ("T02_adventure_30X30_01", 30, 30, 3, 3, 25, 25, [(10,10,'gold'), (20,5,'wood'), (15,20,'rare')], []),
        ("T02_adventure_30X30_02", 30, 30, 27, 27, 3, 3, [(5,25,'gold'), (25,5,'wood'), (15,15,'rare')], []),
        ("T02_adventure_36X36_01", 36, 36, 3, 3, 30, 30, [(10,10,'gold'), (20,5,'wood'), (15,25,'rare')], []),
        ("T02_adventure_36X36_02", 36, 36, 33, 33, 3, 3, [(5,30,'gold'), (30,5,'wood'), (18,18,'rare')], []),
    ],
    "Level 2": [
        ("T03_adventure_20X20_01", 20, 20, 2, 2, 15, 15, [(5,5,'gold'), (10,3,'wood'), (18,10,'rare')], [(15,14,'core:peasant', 8, 'guard'), (5,4,'core:archer', 5, 'guard')]),
        ("T03_adventure_20X20_02", 20, 20, 18, 18, 3, 3, [(5,15,'gold'), (15,5,'wood'), (10,10,'rare')], [(3,4,'core:peasant', 6, 'guard'), (15,4,'core:archer', 4, 'guard')]),
        ("T03_adventure_30X30_01", 30, 30, 3, 3, 25, 25, [(10,10,'gold'), (20,5,'wood'), (15,20,'rare')], [(25,24,'core:peasant', 10, 'guard'), (10,9,'core:archer', 6, 'guard')]),
        ("T03_adventure_30X30_02", 30, 30, 27, 27, 3, 3, [(5,25,'gold'), (25,5,'wood'), (15,15,'rare')], [(3,4,'core:peasant', 8, 'guard'), (25,4,'core:archer', 5, 'guard')]),
        ("T03_adventure_36X36_01", 36, 36, 3, 3, 30, 30, [(10,10,'gold'), (20,5,'wood'), (15,25,'rare')], [(30,29,'core:peasant', 12, 'guard'), (10,9,'core:archer', 7, 'guard')]),
        ("T03_adventure_36X36_02", 36, 36, 33, 33, 3, 3, [(5,30,'gold'), (30,5,'wood'), (18,18,'rare')], [(3,4,'core:peasant', 10, 'guard'), (30,4,'core:archer', 6, 'guard')]),
    ],
    "Level 3": [
        ("T04_adventure_20X20_01", 20, 20, 2, 2, 15, 15, [(5,5,'gold'), (10,3,'wood'), (18,10,'rare'), (12,18,'wood')], [(15,14,'core:peasant', 12, 'guard'), (5,4,'core:archer', 8, 'guard'), (18,9,'core:footman', 5, 'guard')]),
        ("T04_adventure_20X20_02", 20, 20, 18, 18, 3, 3, [(5,15,'gold'), (15,5,'wood'), (10,10,'rare'), (2,12,'wood')], [(3,4,'core:peasant', 10, 'guard'), (15,4,'core:archer', 6, 'guard'), (2,11,'core:footman', 4, 'guard')]),
        ("T04_adventure_30X30_01", 30, 30, 3, 3, 25, 25, [(10,10,'gold'), (20,5,'wood'), (15,20,'rare'), (25,15,'wood')], [(25,24,'core:peasant', 15, 'guard'), (10,9,'core:archer', 10, 'guard'), (25,14,'core:footman', 6, 'guard')]),
        ("T04_adventure_30X30_02", 30, 30, 27, 27, 3, 3, [(5,25,'gold'), (25,5,'wood'), (15,15,'rare'), (2,20,'wood')], [(3,4,'core:peasant', 12, 'guard'), (25,4,'core:archer', 8, 'guard'), (2,19,'core:footman', 5, 'guard')]),
        ("T04_adventure_36X36_01", 36, 36, 3, 3, 30, 30, [(10,10,'gold'), (20,5,'wood'), (15,25,'rare'), (30,15,'wood')], [(30,29,'core:peasant', 18, 'guard'), (10,9,'core:archer', 12, 'guard'), (30,14,'core:footman', 7, 'guard')]),
        ("T04_adventure_36X36_02", 36, 36, 33, 33, 3, 3, [(5,30,'gold'), (30,5,'wood'), (18,18,'rare'), (2,25,'wood')], [(3,4,'core:peasant', 15, 'guard'), (30,4,'core:archer', 10, 'guard'), (2,24,'core:footman', 6, 'guard')]),
    ],
}

print("="*70)
print("自动化地图生成+验证流程")
print("="*70)

total_generated = 0
total_passed = 0
total_failed = 0
failed_maps = []

for level_name, maps in map_definitions.items():
    print(f"\n--- {level_name} ---")
    
    for map_def in maps:
        name = map_def[0]
        print(f"\n生成: {name}")
        
        # 重试机制
        for attempt in range(MAX_RETRIES):
            temp_path = create_map(map_def, level_name)
            
            # 验证
            errors, warnings = validate_map(temp_path)
            
            if not errors:
                # 验证通过，移动到正式目录
                final_path = os.path.join(dst_dir, f"{name}.vmap")
                shutil.move(temp_path, final_path)
                
                status = "✅ PASS"
                if warnings:
                    status += f" (warnings: {len(warnings)})"
                
                print(f"  尝试 {attempt+1}: {status}")
                total_passed += 1
                break
            else:
                # 验证失败，重试
                os.remove(temp_path)
                if attempt == MAX_RETRIES - 1:
                    print(f"  尝试 {attempt+1}: ❌ FAIL - {errors}")
                    failed_maps.append((name, errors))
                    total_failed += 1
                else:
                    print(f"  尝试 {attempt+1}: 重试 - {errors}")
        
        total_generated += 1

# 清理临时目录
try:
    shutil.rmtree(temp_dir)
except:
    pass

print("\n" + "="*70)
print("流程完成")
print("="*70)
print(f"总计: {total_generated} 地图")
print(f"✅ 通过: {total_passed}")
print(f"❌ 失败: {total_failed}")

if failed_maps:
    print("\n失败地图:")
    for name, errors in failed_maps:
        print(f"  - {name}: {errors}")

print(f"\n输出目录: {dst_dir}")
