#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H3 patch ① 接线补全 (2026-09-14):
  08-17 的 removeQuery 函数体一直是"游离实现": header 里声明被注释, 且 BattleResultProcessor
  L401 实际仍调 popIfTop → 真实挂点 = PvP 时一方 CBattleQuery 被 levelup 等嵌套 query 压住,
  popIfTop 对该方静默跳过, onRemoval 只一次, remainingBattleQueriesCount 2→1 永久挂住。

本脚本补全接线 (双树 vcmi-native-build + vcmi-native):
  (1) server/queries/QueriesProcessor.h: '//void removeQuery' → 真实声明
  (2) server/battles/BattleResultProcessor.cpp L401: popIfTop(battleQuery) → removeQuery(battleQuery)
并对两个文件先做 .bak.H3.20260914 备份 (仅首次)。
"""
import os
import shutil

TREES = ["/home/administrator/vcmi-native-build", "/home/administrator/vcmi-native"]
BAK = ".bak.H3.20260914"

H_REL = "server/queries/QueriesProcessor.h"
BRP_REL = "server/battles/BattleResultProcessor.cpp"

H_OLD = "//void removeQuery"
H_NEW = "void removeQuery(QueryPtr query); // ML H3 (2026-09-14): 任意位置强制移除 + 每玩家各调一次 onRemoval (PvP 战斗结算)"

BRP_OLD = "gameHandler->queries->popIfTop(battleQuery); // Workaround to remove battle query for AI case. TODO Think of a cleaner solution."
BRP_NEW = (
    "// ML H3 fix (2026-09-14): popIfTop -> removeQuery。PvP 时一方栈顶被 levelup 等嵌套 query 压住,\n"
    "\t// popIfTop 对该方静默跳过 -> CBattleQuery 只 onRemoval 一次 -> remainingBattleQueriesCount 2->1 永久挂住\n"
    "\t// (BattleEnded 不发 -> currentBattles 残留 -> simturns 占城全拒 + checkVictoryLossConditions 不跑)。\n"
    "\t// removeQuery 任意位置 std::find 强制从每个持有玩家栈移除并各调一次 onRemoval (PvE players=1 / PvP=2,\n"
    "\t// addPlayer 已用 isValidPlayer 过滤 NEUTRAL); 二次 finalize 由 battleFinalize finishingBattles.count 兜底。\n"
    "\tgameHandler->queries->removeQuery(battleQuery);"
)


def backup_once(path):
    bak = path + BAK
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        print(f"backup: {bak}")
    else:
        print(f"backup exists: {bak}")


def patch_file(path, old, new, marker):
    src = open(path, encoding="utf-8").read()
    if marker in src and old not in src:
        print(f"  already patched: {path}")
        return
    if old not in src:
        print(f"ERROR: anchor not found in {path}")
        raise SystemExit(1)
    if src.count(old) != 1:
        print(f"ERROR: anchor not unique ({src.count(old)}x) in {path}")
        raise SystemExit(1)
    open(path, "w", encoding="utf-8").write(src.replace(old, new, 1))
    print(f"  patched: {path}")


for tree in TREES:
    print(f"== {tree}")
    h = os.path.join(tree, H_REL)
    brp = os.path.join(tree, BRP_REL)
    backup_once(h)
    backup_once(brp)
    patch_file(h, H_OLD, H_NEW, "ML H3 (2026-09-14)")
    patch_file(brp, BRP_OLD, BRP_NEW, "ML H3 fix (2026-09-14): popIfTop -> removeQuery")

# 校验
for tree in TREES:
    h = open(os.path.join(tree, H_REL), encoding="utf-8").read()
    brp = open(os.path.join(tree, BRP_REL), encoding="utf-8").read()
    assert "void removeQuery(QueryPtr query);" in h, f"header decl missing: {tree}"
    assert "//void removeQuery" not in h, f"old comment still present: {tree}"
    assert "queries->removeQuery(battleQuery);" in brp, f"call site missing: {tree}"
    assert BRP_OLD not in brp, f"old popIfTop call still present: {tree}"
    print(f"verified: {tree}")

print("WIRE_DONE")
