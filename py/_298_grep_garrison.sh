#!/bin/bash
# #298 S 路线读码: CGarrisonDialogQuery 创建点 + makeGarrisonDialog 调用点 + NK2 上下文 (09-23 只读)
set -u
echo "=== CGarrisonDialogQuery 所有创建点 ==="
grep -rn "CGarrisonDialogQuery" /home/administrator/vcmi-native/server/ --include="*.cpp" --include="*.h" 2>/dev/null | grep -v Binary | head -10
echo ""
echo "=== makeGarrisonDialog 所有调用点 ==="
grep -rn "makeGarrisonDialog" /home/administrator/vcmi-native/server/ /home/administrator/vcmi-native/lib/ --include="*.cpp" --include="*.h" 2>/dev/null | grep -v Binary | head -10
echo ""
echo "=== makeGarrisonDialog 函数签名 ==="
grep -n "makeGarrisonDialog" /home/administrator/vcmi-native/server/CGameHandler.h
echo ""
echo "=== NK2 AIGateway.cpp:1570-1595 (ML-wait 上下文) ==="
sed -n '1570,1595p' /home/administrator/vcmi-native/AI/Nullkiller2/AIGateway.cpp
echo ""
echo "=== NK2 AIGateway.cpp:250-262 (Exchange 描述构造) ==="
sed -n '250,262p' /home/administrator/vcmi-native/AI/Nullkiller2/AIGateway.cpp
