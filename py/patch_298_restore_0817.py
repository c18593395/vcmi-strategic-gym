#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""恢复被 09-19 上游同步冲掉的 3 处本地修复（#298 收官，09-23）。

背景
----
ML 修复以「工作区改动」形式存在，09-19 上游同步把下面 3 处静默覆盖了。
生产编译树 = /home/administrator/vcmi-native（编 rel/），**不是** vcmi-native-build（08-02 陈旧树）。

修复清单
--------
1. server/CGameHandler.cpp `levelUpHero`
   08-17「AI 玩家升级自动选第一个技能」丢失 → 改为按新上游结构重实现：
   在 `!isValidPlayer()` 之外再补 AI（非 human）分支。
   原为防：NK2 answerQuery 持锁死锁 → 升级查询不关闭 → 压住 CBattleQuery → 刷屏卡死。

2. server/battles/BattleResultProcessor.cpp `endBattleConfirm`
   08-17「battleResultAccepted 改用 removeQuery」被回退成上游 popIfTop
   （popIfTop 仅栈顶语义，被嵌套查询压住时永久 FAIL → 战斗查询残留）。

3. server/queries/QueriesProcessor.cpp `removeQuery`
   09-14「删 removalDone 守卫」丢失 → PvP 共享 CBattleQuery 的 onRemoval 只调一次
   → remainingBattleQueriesCount 欠减 → BattleEnded 永不发 → currentBattles 残留
   （踩坑 #228）。**依赖 ②**：removeQuery 必须重新成为唯一调用点。

用法
----
    python py/patch_298_restore_0817.py [--root <vcmi-native 路径>] [--rollback]

幂等：已打过则 skip。每次写入前自动备份 <file>.bak_298restore。
"""
import argparse
import os
import shutil
import sys

DEFAULT_ROOT = os.environ.get("DEFAULT_ROOT", "/home/administrator/vcmi-native")
BAK = ".bak_298restore"

CG = "server/CGameHandler.cpp"
BR = "server/battles/BattleResultProcessor.cpp"
QP = "server/queries/QueriesProcessor.cpp"

# ---------------- ① CGameHandler::levelUpHero ----------------
CG_ANCHOR = "if (!hero->getOwner().isValidPlayer())"
CG_NEW = [
    "// ML fix (2026-08-17, 09-23 恢复): AI 玩家升级自动选第一个技能 (无头服务器模式)。",
    "// 防 NK2 heroGotLevel answeredQuery 持 CGameState 共享锁死锁 → 升级查询永不关闭",
    "// → 压住 CBattleQuery → battleResultAccepted popIfTop FAIL → \"has to answer queries\" 刷屏。",
    "// AI 无需人工选技能: 直接取第一个并完成 (客户端模式 AI 独立进程自己答, 不受影响)。",
    "if (!hero->getOwner().isValidPlayer() || !gameInfo().getPlayerState(hero->getOwner())->isHuman())",
]

# ---------------- ② BattleResultProcessor 调用点 ----------------
BR_DROP_PREFIX = 'fprintf(stderr, "[ML-stk] caller=BR-battleResultAIcase'
BR_OLD_PREFIX = "gameHandler->queries->popIfTop(battleQuery);"
BR_NEW = [
    "// ML fix (2026-08-17, 09-23 恢复): popIfTop 仅栈顶语义, 被嵌套查询 (战利品/升级) 压住时永久 FAIL",
    "// → 战斗查询残留 → \"has to answer queries\" 刷屏 → NK2 动作全拒 → 采集卡死。",
    "// 改 removeQuery 任意位置强制移除 (battleQuery->result 已设置, onRemoval 执行 battleFinalize)。",
    "gameHandler->queries->removeQuery(battleQuery);",
]

# ---------------- ③ QueriesProcessor::removeQuery 去守卫 ----------------
QP_GUARD_COMMENT_OLD = "// 1) onRemoval 只调一次: 多玩家查询二次触发 battleFinalize → 段错误。"
QP_GUARD_COMMENT_NEW = [
    "// 1) [09-14 修正/09-23 恢复] onRemoval 每玩家各调一次 (对齐上游 popQuery per-player 语义):",
    "//    旧 removalDone 守卫让 PvP 共享 query 只调一次 → remainingBattleQueriesCount 欠减",
    "//    → BattleEnded 永不发 → currentBattles 残留 (+ 无人判 LOSER)。见踩坑 #228。",
]
QP_GUARD_VAR = "bool removalDone = false;"
QP_GUARD_SEQ = ["if(!removalDone)", "{", "query->onRemoval(player);", "removalDone = true;", "}"]


def indent_of(line):
    return line[:len(line) - len(line.lstrip())]


def patch_cg(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    for i, ln in enumerate(lines):
        if ln.strip() == CG_ANCHOR:
            ind = indent_of(ln)
            lines[i:i + 1] = [ind + s for s in CG_NEW]
            open(path, "w", encoding="utf-8").write("\n".join(lines))
            return "patched"
    if any(CG_NEW[-1] in ln for ln in lines):
        return "already"
    return "anchor-missing"


def patch_br(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    hit = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith(BR_OLD_PREFIX):
            hit = i
            break
    if hit is None:
        return "already" if any("removeQuery(battleQuery);" in ln for ln in lines) else "anchor-missing"
    ind = indent_of(lines[hit])
    new = []
    if hit > 0 and lines[hit - 1].strip().startswith(BR_DROP_PREFIX):
        hit -= 1                                   # 同时删掉 #298 留下的游离打点行
    new = [ind + s for s in BR_NEW]
    lines[hit:hit + 2] = new
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    return "patched"


def patch_qp(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    out, i, changed = [], 0, False
    while i < len(lines):
        s = lines[i].strip()
        if s == QP_GUARD_VAR:
            i += 1
            changed = True
            continue
        if s == QP_GUARD_SEQ[0] and i + 4 < len(lines) and \
                [lines[i + k].strip() for k in range(5)] == QP_GUARD_SEQ:
            out.append(indent_of(lines[i + 2]) + QP_GUARD_SEQ[2])   # 只留 onRemoval 调用
            i += 5
            changed = True
            continue
        if s == QP_GUARD_COMMENT_OLD:
            ind = indent_of(lines[i])
            out.extend(ind + c for c in QP_GUARD_COMMENT_NEW)
            i += 1
            changed = True
            continue
        out.append(lines[i])
        i += 1
    if not changed:
        return "already" if QP_GUARD_VAR not in "\n".join(lines) else "anchor-missing"
    open(path, "w", encoding="utf-8").write("\n".join(out))
    return "patched"


def backup(path):
    if not os.path.exists(path + BAK):
        shutil.copy2(path, path + BAK)


def rollback(root):
    for rel in (CG, BR, QP):
        p = os.path.join(root, rel)
        if os.path.exists(p + BAK):
            shutil.copy2(p + BAK, p)
            os.utime(p, None)   # 坑: copy2 保留备份的旧 mtime → make 认为无需重编(.so 与源码不一致)。必须刷新。
            print("restored from bak (mtime refreshed): %s" % rel)
        else:
            print("no bak, skip: %s" % rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--rollback", action="store_true")
    args = ap.parse_args()

    root = args.root
    if not os.path.isdir(root):
        print("root not found: %s" % root, file=sys.stderr)
        return 2
    if args.rollback:
        rollback(root)
        return 0

    results = {}
    for rel, fn in ((CG, patch_cg), (BR, patch_br), (QP, patch_qp)):
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            results[rel] = "file-missing"
            continue
        backup(p)
        results[rel] = fn(p)

    for rel, r in results.items():
        print("%-46s %s" % (rel, r))

    bad = [k for k, v in results.items() if v in ("anchor-missing", "file-missing")]
    if bad:
        print("\n结论：有锚点未命中 —— 源码可能已变，人工核对后再跑。", file=sys.stderr)
        return 1

    # 写后校验
    cg = open(os.path.join(root, CG), encoding="utf-8").read()
    br = open(os.path.join(root, BR), encoding="utf-8").read()
    qp = open(os.path.join(root, QP), encoding="utf-8").read()
    checks = [
        ("CG: AI 分支已加", "!gameInfo().getPlayerState(hero->getOwner())->isHuman()" in cg),
        ("BR: 调用点=removeQuery", "queries->removeQuery(battleQuery);" in br),
        ("BR: 无残留 popIfTop(battleQuery)", "popIfTop(battleQuery)" not in br),
        ("QP: 守卫已删", "bool removalDone" not in qp),
        ("QP: onRemoval 仍在", "query->onRemoval(player);" in qp),
    ]
    for name, ok in checks:
        print("  [%s] %s" % ("OK" if ok else "FAIL", name))
    if not all(ok for _, ok in checks):
        print("\n校验失败 —— 请 --rollback 回退。", file=sys.stderr)
        return 1
    print("\n结论：3 处恢复完成并通过校验。")
    return 0


if __name__ == "__main__":
    sys.exit(main())