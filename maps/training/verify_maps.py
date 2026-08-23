import zipfile, json, os
import sys

training_dir = "D:/Bigdata/hero3_fresh/Maps/training"
vmap_files = sorted([f for f in os.listdir(training_dir) if f.endswith('.vmap')])

print(f"验证 {len(vmap_files)} 个地图文件...\n")

errors = []
warnings = []

for vmap_file in vmap_files:
    filepath = os.path.join(training_dir, vmap_file)
    print(f"=== {vmap_file} ===")
    
    try:
        with zipfile.ZipFile(filepath) as z:
            # 检查必要文件
            required_files = ['header.json', 'surface_terrain.json', 'objects.json']
            for rf in required_files:
                if rf not in z.namelist():
                    errors.append(f"{vmap_file}: 缺少 {rf}")
                    continue
            
            # 读取数据
            header = json.loads(z.read('header.json'))
            terrain = json.loads(z.read('surface_terrain.json'))
            objects = json.loads(z.read('objects.json'))
            
            # 检查 header
            if 'name' not in header:
                errors.append(f"{vmap_file}: header 缺少 name")
            if 'mapLevels' not in header:
                errors.append(f"{vmap_file}: header 缺少 mapLevels")
            else:
                surface = header['mapLevels'].get('surface', {})
                w = surface.get('width', 0)
                h = surface.get('height', 0)
                print(f"  尺寸: {w}x{h}")
            
            # 检查 terrain
            if len(terrain) != h:
                errors.append(f"{vmap_file}: terrain 行数 {len(terrain)} != {h}")
            for y, row in enumerate(terrain):
                if len(row) != w:
                    errors.append(f"{vmap_file}: terrain 第{y}行列数 {len(row)} != {w}")
                    break
            
            # 检查地形代码
            valid_codes = {'gr24_', 'wt00_', 'ro00_', 'rd00_', 'sa00_', 'dt01_'}
            terrain_codes = set()
            for row in terrain:
                terrain_codes.update(row)
            invalid_codes = terrain_codes - valid_codes
            if invalid_codes:
                warnings.append(f"{vmap_file}: 未知地形代码 {invalid_codes}")
            print(f"  地形代码: {terrain_codes}")
            
            # 检查对象
            hero_count = sum(1 for k in objects if k.startswith('hero_'))
            town_count = sum(1 for k in objects if k.startswith('town_'))
            mine_count = sum(1 for k in objects if k.startswith('mine_'))
            resource_count = sum(1 for k in objects if k.startswith('resource_'))
            monster_count = sum(1 for k in objects if k.startswith('monster_'))
            
            print(f"  对象: {hero_count}英雄, {town_count}城镇, {mine_count}矿, {resource_count}资源, {monster_count}野怪")
            
            # 检查对象位置
            for obj_name, obj_data in objects.items():
                x = obj_data.get('x', -1)
                y = obj_data.get('y', -1)
                if x < 0 or x >= w or y < 0 or y >= h:
                    errors.append(f"{vmap_file}: {obj_name} 位置 ({x},{y}) 超出地图范围")
            
            # 检查必要对象
            if 'hero_0' not in objects:
                errors.append(f"{vmap_file}: 缺少 hero_0")
            if 'town_0' not in objects:
                warnings.append(f"{vmap_file}: 缺少 town_0")
            
            print(f"  状态: 通过")
            
    except Exception as e:
        errors.append(f"{vmap_file}: 解析错误 - {e}")
        print(f"  状态: 失败 - {e}")

print("\n" + "="*60)
print("验证结果汇总:")
print("="*60)

if errors:
    print(f"\n❌ 错误 ({len(errors)}):")
    for err in errors:
        print(f"  - {err}")
else:
    print("\n✅ 无错误")

if warnings:
    print(f"\n⚠️  警告 ({len(warnings)}):")
    for warn in warnings:
        print(f"  - {warn}")
else:
    print("\n✅ 无警告")

print(f"\n总计: {len(vmap_files)} 地图, {len(errors)} 错误, {len(warnings)} 警告")
