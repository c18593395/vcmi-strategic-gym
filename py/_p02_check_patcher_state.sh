#!/bin/bash
# P0-2 对照实验: 查三套补丁 + 08-17 恢复 叠加状态，设计干净 A/B
B=/home/administrator/vcmi-native
echo "=== A 档当前源码标记 ==="
echo -n "  [Client.cpp] 方案1标记: "
grep -c 'ML fix (09-23, #298)' $B/client/Client.cpp
echo -n "  [AIGateway] ML-upg 熔断: "
grep -c 'ML-upg' $B/AI/Nullkiller2/AIGateway.cpp
echo -n "  [QueriesProcessor] ML-stk: "
grep -c 'ML-stk' $B/server/queries/QueriesProcessor.cpp
echo -n "  [CGameHandler] levelUpHero: "
grep -c 'levelUpHero' $B/server/CGameHandler.cpp
echo -n "  [BattleResultProcessor] removeQuery: "
grep -c 'removeQuery' $B/server/battles/BattleResultProcessor.cpp
echo

echo "=== .bak 备份谱系（区分三套 vs 08-17 恢复）==="
ls -la $B/client/Client.cpp.bak_* $B/AI/Nullkiller2/AIGateway.cpp.bak_* \
       $B/server/queries/QueriesProcessor.cpp.bak_* $B/server/CGameHandler.cpp.bak_* \
       $B/server/battles/BattleResultProcessor.cpp.bak_* 2>/dev/null

echo
echo "=== 关键: 各 .bak 是否含三套补丁标记（判断 .bak 是哪一档的备份）==="
echo -n "  .bak_upg298[AIGateway] 含 ML-upg? "
grep -c 'ML-upg' $B/AI/Nullkiller2/AIGateway.cpp.bak_upg298 2>/dev/null || echo " 无此文件"
echo -n "  .bak_netfix298[Client.cpp] 含方案1? "
grep -c 'ML fix (09-23, #298)' $B/client/Client.cpp.bak_netfix298 2>/dev/null || echo " 无此文件"
echo -n "  .bak_stk298[QueriesProcessor] 含 ML-stk? "
grep -c 'ML-stk' $B/server/queries/QueriesProcessor.cpp.bak_stk298 2>/dev/null || echo " 无此文件"
echo -n "  .bak_298restore[CGameHandler] 含 levelUpHero? "
grep -c 'levelUpHero' $B/server/CGameHandler.cpp.bak_298restore 2>/dev/null || echo " 无此文件"

echo
echo "=== rel/ 重编目标 ==="
ls -d $B/rel 2>/dev/null && echo "rel/ OK"
echo
echo "=== cmake preset / 构建 ==="
ls $B/CMakeCache.txt $B/rel/CMakeCache.txt 2>/dev/null
