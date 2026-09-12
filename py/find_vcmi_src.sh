#!/bin/bash
# 查找 vcmi-native 源码结构
echo "=== vcmi-native top-level ==="
ls /home/administrator/vcmi-native/ 2>/dev/null | head -30
echo ""
echo "=== vcmi-native/src top ==="
ls /home/administrator/vcmi-native/src/ 2>/dev/null | head -30
echo ""
echo "=== find *.cpp with MapLoader in name ==="
find /home/administrator/vcmi-native -name "*MapLoader*" 2>/dev/null | head -20
echo ""
echo "=== find CMapLoaderJson* ==="
find /home/administrator/vcmi-native -name "*CMapLoader*" 2>/dev/null | head -20
echo ""
echo "=== grep surface_terrain in entire vcmi-native (all extensions) ==="
grep -rn "surface_terrain" /home/administrator/vcmi-native/ --include="*.cpp" --include="*.h" --include="*.hpp" 2>/dev/null | head -10
echo ""
echo "=== grep mapLevels ==="
grep -rn "mapLevels" /home/administrator/vcmi-native/ --include="*.cpp" --include="*.h" --include="*.hpp" 2>/dev/null | head -10
echo ""
echo "=== grep terrainFile / terrain file ==="
grep -rn "terrainFile\|terrain_file\|terrainJson" /home/administrator/vcmi-native/ --include="*.cpp" --include="*.h" 2>/dev/null | head -10
