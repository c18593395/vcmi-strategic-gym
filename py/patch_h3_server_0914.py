#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H3 patch ①: server/queries/QueriesProcessor.cpp removeQuery()
修复根因 C: 08-17 补丁遗留的 removalDone 守卫导致 PvP 多玩家共享 CBattleQuery
  的 onRemoval 只调一次 → remainingBattleQueriesCount 欠减 → BattleEnded 永不发。

修复: 去掉 removalDone 守卫, 每个实际持有该 query 的玩家各调一次 onRemoval。
目标: /home/administrator/vcmi-native-build/server/queries/QueriesProcessor.cpp (tab 缩进)
"""
import sys
import textwrap

F = "/home/administrator/vcmi-native-build/server/queries/QueriesProcessor.cpp"
src = open(F, encoding="utf-8").read()

old = textwrap.dedent("""
void QueriesProcessor::removeQuery(QueryPtr query)
{
	// ML fix (2026-08-17): 任意位置强制移除 (战斗结算兜底)。
	// 1) onRemoval 只调一次: 多玩家查询二次触发 battleFinalize → 段错误。
	// 2) 移除后必须触发暴露链 (对齐 popQuery): 否则被压的 visitQuery 永不 onExposure
	//    → 访问永不结束 (obj=1 永久) → 怪物战斗收尾断 (battleFinished 不触发)。
	if(!query)
		return;
	bool removalDone = false;
	for(PlayerColor player : query->players)
	{
		auto & v = queries[player];
		auto it = std::find(v.begin(), v.end(), query);
		if(it != v.end())
		{
			v.erase(it);
			if(!removalDone)
			{
				query->onRemoval(player);
				removalDone = true;
			}
			auto nextQuery = topQuery(player);
			if(nextQuery)
				nextQuery->onExposure(query);
		}
	}
}
""").lstrip("\n")

new = textwrap.dedent("""
void QueriesProcessor::removeQuery(QueryPtr query)
{
	// ML H3 fix (2026-09-14): 去掉 removalDone 守卫, 每个实际持有该 query 的玩家各调一次 onRemoval。
	// 根因 C: PvP CBattleQuery 共享于红蓝两栈, 旧 removalDone 让 onRemoval 只调一次,
	//   remainingBattleQueriesCount 2→1 永久挂住 → BattleEnded 永不发 → currentBattles 残留
	//   → simturns 占城全拒 + checkVictoryLossConditions 永不跑 → 无人判 LOSER。
	// 下游 battleFinalize (BattleResultProcessor.cpp) 已有 finishingBattles.count(battleID)==0 return 兜底,
	// 二次调用幂等安全 (对齐上游 popQuery per-player 语义)。
	if(!query)
		return;
	for(PlayerColor player : query->players)
	{
		auto & v = queries[player];
		auto it = std::find(v.begin(), v.end(), query);
		if(it != v.end())
		{
			v.erase(it);
			query->onRemoval(player);
			auto nextQuery = topQuery(player);
			if(nextQuery)
				nextQuery->onExposure(query);
		}
	}
}
""").lstrip("\n")

if old in src:
    src = src.replace(old, new, 1)
    open(F, "w", encoding="utf-8").write(src)
    print("patched: removed removalDone guard, onRemoval now per-player")
elif "ML H3 fix (2026-09-14)" in src:
    print("already patched, skip")
else:
    print("ERROR: text drifted. Current removeQuery block:")
    i = src.find("void QueriesProcessor::removeQuery")
    print(src[i:i+700])
    sys.exit(1)

chk = open(F, encoding="utf-8").read()
assert "bool removalDone" not in chk, "guard still present!"
assert "query->onRemoval(player);" in chk, "onRemoval call missing!"
assert "ML H3 fix (2026-09-14)" in chk, "new comment missing!"
print("verified OK")
