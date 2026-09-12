#!/bin/bash
# 引擎侧 CMapLoaderJson 读 terrain 的逻辑
echo '=== CMapLoaderJson terrain 加载 ==='
grep -rn "surface_terrain\|terrain_0\|mapLevels" /home/administrator/vcmi-native/src/server/libs/CMapLoaderJson.cpp 2>/dev/null | head -30

echo ""
echo '=== CMapLoaderJson 是否存在 ==='
ls -la /home/administrator/vcmi-native/src/server/libs/CMapLoaderJson* 2>/dev/null
find /home/administrator/vcmi-native -name "CMapLoaderJson*" 2>/dev/null

echo ""
echo '=== header.json 里 mapLevels 结构 (72X72_02_duel 为例) ==='
python3 -c "
import zipfile, json
z = zipfile.ZipFile('/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps/T06_adventure_72X72_02_duel.vmap')
h = json.loads(z.read('header.json'))
print('mapLevels keys:', list(h.get('mapLevels', {}).keys()))
for k, v in h.get('mapLevels', {}).items():
    print(f'  {k}:', json.dumps(v)[:200])
print('name:', h.get('name'))
"
