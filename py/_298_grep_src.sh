#!/bin/bash
# #298 源码侧 grep: 转换器 random 处理 + MapFormatJson 加载 (09-23 只读)
set -u
echo "=== h3m2vmap 转换器 random 处理 ==="
grep -n "random\|Random" /home/administrator/vcmi-native/tools/h3m2vmap/main.cpp 2>/dev/null | head -20
echo ""
echo "=== MapFormatJson: randomTown/randomHero ==="
grep -n "randomTown\|RANDOM_TOWN\|randomHero\|RANDOM_HERO" /home/administrator/vcmi-native/lib/mapping/MapFormatJson.cpp 2>/dev/null | head -10
echo ""
echo "=== VCMI config: randomTown identifier ==="
grep -rn "randomTown" /home/administrator/vcmi-native/config/ 2>/dev/null | head -8
echo ""
echo "=== MapReaderH3M randomize (H3M 加载期随机化) ==="
grep -n "randomize\|Randomize" /home/administrator/vcmi-native/lib/mapping/MapReaderH3M.cpp 2>/dev/null | head -10
echo ""
echo "=== vmap 加载入口: MapFormatJson 读 objects 的 type 解析 ==="
grep -n "addObject\|parseObjectName\|identifier" /home/administrator/vcmi-native/lib/mapping/MapFormatJson.cpp 2>/dev/null | head -15
