#!/bin/bash
# 检查所有 T06 地图位置 + T05 对照 zip 内容
echo '=== 所有 T06 vmap 位置 (全盘) ==='
find /home/administrator -name 'T06*.vmap' 2>/dev/null | sort

echo ""
echo '=== T05 对照 zip 内容 ==='
python3 -c "
import zipfile
import os
maps_dir = '/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps'
for f in sorted(os.listdir(maps_dir)):
    if f.startswith('T05'):
        z = zipfile.ZipFile(os.path.join(maps_dir, f))
        names = sorted(z.namelist())
        has_t0 = any('terrain_0' in n for n in names)
        has_st = any('surface_terrain' in n for n in names)
        print(f'{f}: files={len(names)} terrain_0={has_t0} surface_terrain={has_st}')
        break
" 2>&1

echo ""
echo '=== T06 文件在 v13/maps 的内容 ==='
python3 -c "
import zipfile
import os
maps_dir = '/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps'
for f in sorted(os.listdir(maps_dir)):
    if f.startswith('T06'):
        z = zipfile.ZipFile(os.path.join(maps_dir, f))
        names = sorted(z.namelist())
        has_t0 = any('terrain_0' in n for n in names)
        has_st = any('surface_terrain' in n for n in names)
        print(f'{f}: files={len(names)} terrain_0={has_t0} surface_terrain={has_st} names={names}')
" 2>&1
