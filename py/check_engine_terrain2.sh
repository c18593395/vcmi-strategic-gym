#!/bin/bash
# 在 WSL 侧 vcmi-native 源码中搜索 terrain 文件读取逻辑
set -e
WSL_VCMI=""
for d in /home/administrator/vcmi-native /home/administrator/vcmi-native-build /home/administrator/vcmi-workspace/vcmi-native; do
  if [ -d "$d" ]; then
    WSL_VCMI="$d"
    break
  fi
done
if [ -z "$WSL_VCMI" ]; then
  echo "vcmi-native not found"
  exit 1
fi
echo "=== vcmi dir: $WSL_VCMI ==="

# 搜索 surface_terrain / terrain_0 / mapLevels 相关代码
echo "--- grep surface_terrain ---"
grep -rn "surface_terrain" "$WSL_VCMI/src" 2>/dev/null || echo "(no match)"
echo "--- grep terrain_0 ---"
grep -rn "terrain_0" "$WSL_VCMI/src" 2>/dev/null || echo "(no match)"
echo "--- grep mapLevels ---"
grep -rn "mapLevels" "$WSL_VCMI/src" 2>/dev/null || echo "(no match)"
echo "--- grep CMapLoaderJson (class def) ---"
grep -rn "CMapLoaderJson" "$WSL_VCMI/src" 2>/dev/null | head -20 || echo "(no match)"
echo "--- find CMapLoaderJson files ---"
find "$WSL_VCMI/src" -name "*CMapLoaderJson*" -o -name "*MapLoader*" 2>/dev/null || echo "(no match)"
echo "--- grep loadMap / loadTerrain ---"
grep -rn "loadMap\|loadTerrain\|terrainFile" "$WSL_VCMI/src" 2>/dev/null | head -30 || echo "(no match)"
