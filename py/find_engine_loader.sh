#!/bin/bash
# 找引擎侧 CMapLoaderJson 实际位置 + 读 terrain 逻辑
echo '=== find CMapLoaderJson ==='
find /home/administrator -name "CMapLoaderJson*" 2>/dev/null | head -10

echo ""
echo '=== vcmi-native-build 侧 ==='
find /home/administrator -path "*/vcmi-native*" -name "CMapLoaderJson*" 2>/dev/null | head -10

echo ""
echo '=== 搜 surface_terrain 在引擎源码 ==='
grep -rn "surface_terrain" /home/administrator/vcmi-native*/src/ 2>/dev/null | grep -v ".o:" | head -20

echo ""
echo '=== 搜 terrain_0 在引擎源码 ==='
grep -rn "terrain_0" /home/administrator/vcmi-native*/src/ 2>/dev/null | grep -v ".o:" | head -20

echo ""
echo '=== mapLevels 在引擎源码 ==='
grep -rn "mapLevels" /home/administrator/vcmi-native*/src/ 2>/dev/null | grep -v ".o:" | head -20
