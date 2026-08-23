import zipfile, json, os
from collections import deque

def is_passable(terrain, x, y, w, h):
    """检查地形是否可通行"""
    if x < 0 or x >= w or y < 0 or y >= h:
        return False
    code = terrain[y][x]
    # 草地和道路可通行，水、岩石、沙地不可通行
    return code in ('gr24_', 'rd00_')

def bfs_path_exists(terrain, start_x, start_y, target_x, target_y, w, h):
    """BFS检查是否存在路径"""
    if not is_passable(terrain, start_x, start_y, w, h):
        return False, 0
    if not is_passable(terrain, target_x, target_y, w, h):
        # 目标格可能是矿/资源，需要特殊处理
        # 矿和资源虽然地形可能不可通行，但可以访问
        pass
    
    visited = set()
    queue = deque([(start_x, start_y, 0)])
    visited.add((start_x, start_y))
    
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    while queue:
        x, y, dist = queue.popleft()
        
        if x == target_x and y == target_y:
            return True, dist
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in visited and is_passable(terrain, nx, ny, w, h):
                visited.add((nx, ny))
                queue.append((nx, ny, dist + 1))
    
    return False, 0

training_dir = "D:/Bigdata/hero3_fresh/Maps/training"
vmap_files = sorted([f for f in os.listdir(training_dir) if f.endswith('.vmap')])

print("BFS路径可达性测试...\n")
print("="*70)

results = []

for vmap_file in vmap_files:
    filepath = os.path.join(training_dir, vmap_file)
    
    with zipfile.ZipFile(filepath) as z:
        header = json.loads(z.read('header.json'))
        terrain = json.loads(z.read('surface_terrain.json'))
        objects = json.loads(z.read('objects.json'))
    
    surface = header['mapLevels']['surface']
    w = surface['width']
    h = surface['height']
    
    # 获取hero_0位置
    if 'hero_0' not in objects:
        results.append((vmap_file, "SKIP", "无hero_0"))
        continue
    
    hx = objects['hero_0']['x']
    hy = objects['hero_0']['y']
    
    # 测试到各个目标的路径
    test_targets = []
    
    # 矿
    for k, v in objects.items():
        if k.startswith('mine_'):
            test_targets.append((k, v['x'], v['y']))
    
    # 资源点
    for k, v in objects.items():
        if k.startswith('resource_'):
            test_targets.append((k, v['x'], v['y']))
    
    if not test_targets:
        results.append((vmap_file, "SKIP", "无目标"))
        continue
    
    # 测试BFS
    reachable = 0
    total = len(test_targets)
    details = []
    
    for target_name, tx, ty in test_targets:
        found, dist = bfs_path_exists(terrain, hx, hy, tx, ty, w, h)
        if found:
            reachable += 1
            details.append(f"{target_name}: 可达 (距离={dist})")
        else:
            details.append(f"{target_name}: 不可达")
    
    status = "PASS" if reachable == total else "PARTIAL" if reachable > 0 else "FAIL"
    results.append((vmap_file, status, f"{reachable}/{total}"))
    
    print(f"\n{vmap_file}:")
    print(f"  Hero位置: ({hx},{hy})")
    print(f"  可达性: {reachable}/{total}")
    if status != "PASS":
        for d in details:
            if "不可达" in d:
                print(f"    ⚠️  {d}")

print("\n" + "="*70)
print("测试结果汇总:")
print("="*70)

pass_count = sum(1 for _, s, _ in results if s == "PASS")
partial_count = sum(1 for _, s, _ in results if s == "PARTIAL")
fail_count = sum(1 for _, s, _ in results if s == "FAIL")
skip_count = sum(1 for _, s, _ in results if s == "SKIP")

print(f"\n✅ PASS: {pass_count}")
print(f"⚠️  PARTIAL: {partial_count}")
print(f"❌ FAIL: {fail_count}")
print(f"⏭️  SKIP: {skip_count}")

if fail_count > 0:
    print("\n失败地图:")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  - {name}: {detail}")

print(f"\n总计: {len(results)} 地图")
