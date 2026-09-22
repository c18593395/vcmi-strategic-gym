#!/bin/bash
# #298: popIfTop FAIL / MapObjectVisitQuery ML 处理逻辑定位 (09-23 只读)
set -u
echo "=== popIfTop FAIL 日志源 ==="
grep -rn "popIfTop" /home/administrator/vcmi-native/server/ML/ /home/administrator/vcmi-workspace/vcmi_gym/ /home/administrator/vcmi-native/lib/ 2>/dev/null | grep -v Binary | head -15
echo ""
echo "=== MapObjectVisitQuery 处理 (ML 侧) ==="
grep -rn "MapObjectVisitQuery" /home/administrator/vcmi-native/server/ML/ /home/administrator/vcmi-workspace/vcmi_gym/connectors/ 2>/dev/null | grep -v Binary | head -15
echo ""
echo "=== queries popQuery / tryPopQuery 引擎侧 ==="
grep -rn "popIfTop\|tryPopQuery\|popQuery" /home/administrator/vcmi-native/server/queries/*.h /home/administrator/vcmi-native/server/queries/*.cpp 2>/dev/null | head -15
