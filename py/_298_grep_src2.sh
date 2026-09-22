#!/bin/bash
# #298: RANDOM_TOWN 定型阶段 + seed 传递链 (09-23 只读)
set -u
echo "=== Obj::RANDOM_TOWN 在 server/gameState 的定型处理 ==="
grep -rn "RANDOM_TOWN" /home/administrator/vcmi-native/server/ /home/administrator/vcmi-native/lib/gameState/ 2>/dev/null | grep -v Binary | head -15
echo ""
echo "=== randomizeObject / pickNextObject / initObjRandom 相关 ==="
grep -rn "randomizeObject\|pickNext\|RandomObject\|initRandom" /home/administrator/vcmi-native/server/ /home/administrator/vcmi-native/lib/gameState/ /home/administrator/vcmi-native/lib/mapObjects/ 2>/dev/null | grep -v Binary | head -15
echo ""
echo "=== CGTownInstance randomTown 定型 (initTown / RandomFaction) ==="
grep -n "RANDOM_TOWN\|randomize\|RandomTown" /home/administrator/vcmi-native/lib/mapObjects/CGTownInstance.cpp 2>/dev/null | head -10
sed -n '475,495p' /home/administrator/vcmi-native/lib/mapObjects/CGTownInstance.cpp
echo ""
echo "=== seed 传递链: StrategicEnv/ep_runner 是否传 seed ==="
grep -n "seed" /home/administrator/vcmi-workspace/vcmi_gym/envs/v13/strategic_env.py 2>/dev/null | head -10
echo ""
echo "=== threadconnector seed 消费 ==="
grep -n "_seed\|seed" /home/administrator/vcmi-workspace/vcmi_gym/connectors/v13/threadconnector.cpp 2>/dev/null | head -12
