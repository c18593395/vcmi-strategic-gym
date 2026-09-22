#!/bin/bash
# #298: MMAI dialog 应答实现检查 (09-23 只读)
set -u
echo "=== MMAI AI 的 dialog/query 回调处理 ==="
grep -rn "BlockingDialog\|showBlockingDialog\|GarrisonDialog\|ExchangeDialog\|showGarrisonDialog" /home/administrator/vcmi-native/AI/MMAI/ 2>/dev/null | grep -v Binary | head -15
echo ""
echo "=== MMAI 主入口类继承 (CGateway?) ==="
grep -rn "class.*AIGateway\|class.*MMAI.*public" /home/administrator/vcmi-native/AI/MMAI/*.h /home/administrator/vcmi-native/AI/MMAI/**/*.h 2>/dev/null | head -8
echo ""
echo "=== VCMI 标准 AI (AIGateway) 的 BlockingDialog 应答 (对照) ==="
grep -rn "showBlockingDialog" /home/administrator/vcmi-native/AI/ 2>/dev/null | grep -v Binary | grep -v MMAI | head -10
echo ""
echo "=== blue_adventure_ai=MMAI 时 client 侧 AI 实例化 (threadconnector) ==="
grep -n "MMAI\|adventureAI\|AdventureAI" /home/administrator/vcmi-workspace/vcmi_gym/connectors/v13/threadconnector.cpp 2>/dev/null | head -10
