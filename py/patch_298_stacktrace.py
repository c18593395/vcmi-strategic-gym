#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#298 查询栈变更打点插桩 (09-23, 纯 fprintf, 不动逻辑)

目的: 定位"谁在 objectVisited ①→④ 之间移除了 MapObjectVisitQuery"。
- QueriesProcessor 四个变更点各打一行 [ML-stk]:
  PUSH / POP / POP-FAIL / POPIFTOP-HIT / POPIFTOP-FAIL / FORCE-REMOVE
  格式: [ML-stk] <动作> player=<n> depth=<n> <query->toString()>
- 外部调用点加 caller 标签, 用于点名"谁调的"
  (VQ 两处未加标签: 若 POP 行显示 MapObjectVisitQuery 且无 CG-objectVisitedTail 标签,
   即可判定是 VisitQueries onExposure 自 pop)

运行: wsl -u root bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/patch_298_stacktrace.py"
回退: 同命令加 rollback
"""
import os
import shutil
import sys

BASE = os.environ.get("BASE", "/home/administrator/vcmi-native")
QP = BASE + "/server/queries/QueriesProcessor.cpp"
CG = BASE + "/server/CGameHandler.cpp"
BR = BASE + "/server/battles/BattleResultProcessor.cpp"

T = "\t"


def stk(action, expr_players="player.getNum()", expr_query="query->toString().c_str()",
        expr_depth="(int)queries[player].size()"):
    return ('fprintf(stderr, "[ML-stk] %s player=%%d depth=%%d %%s\\n", %s, %s, %s);'
            % (action, expr_players, expr_depth, expr_query))


EDITS = [
    # ---- QueriesProcessor: addQuery 入栈 ----
    (QP,
     T + "queries[player].push_back(query);\n}",
     T + "queries[player].push_back(query);\n" + T + stk("PUSH") + "\n}",
     1),
    # ---- QueriesProcessor: popQuery 成功出栈 ----
    (QP,
     T + "queries[player] -= query;\n" + T + "auto nextQuery = topQuery(player);",
     T + "queries[player] -= query;\n" + T + stk("POP") + "\n" + T + "auto nextQuery = topQuery(player);",
     1),
    # ---- QueriesProcessor: popQuery 失败分支 ----
    (QP,
     T * 3 + 'fprintf(stderr, "  [ML-q]   stack: %s\\n", q->toString().c_str());\n' + T * 2 + "return;",
     T * 3 + 'fprintf(stderr, "  [ML-q]   stack: %s\\n", q->toString().c_str());\n'
     + T * 2 + stk("POP-FAIL") + "\n" + T * 2 + "return;",
     1),
    # ---- QueriesProcessor: popIfTop 命中 ----
    (QP,
     T * 2 + "if(top.get() == &query)\n" + T * 3 + "popQuery(color, top);\n" + T * 2 + "else\n",
     T * 2 + "if(top.get() == &query)\n" + T * 2 + "{\n"
     + T * 3 + stk("POPIFTOP-HIT", "color.getNum()", "query.toString().c_str()", "(int)queries[color].size()") + "\n"
     + T * 3 + "popQuery(color, top);\n" + T * 2 + "}\n" + T * 2 + "else\n",
     1),
    # ---- QueriesProcessor: popIfTop 失败 ----
    (QP,
     T * 3 + "// ML debug (ring 6): popIfTop FAIL = blocking query on top\n",
     T * 3 + "// ML debug (ring 6): popIfTop FAIL = blocking query on top\n"
     + T * 3 + stk("POPIFTOP-FAIL", "color.getNum()", "query.toString().c_str()", "(int)queries[color].size()") + "\n",
     1),
    # ---- QueriesProcessor: removeQuery 强制移除 ----
    (QP,
     T * 3 + "v.erase(it);\n",
     T * 3 + "v.erase(it);\n" + T * 3 + stk("FORCE-REMOVE") + "\n",
     1),
    # ---- 外部调用点 caller 标签 (无缩进锚点, 降低匹配风险) ----
    (CG, "queries->popQuery(dialogQuery);",
     T * 2 + 'fprintf(stderr, "[ML-stk] caller=CG-answerDialog\\n");\n' + T * 2 + "queries->popQuery(dialogQuery);", 1),
    (CG, "queries->popQuery(topQuery);",
     T * 2 + 'fprintf(stderr, "[ML-stk] caller=CG-answerQuery\\n");\n' + T * 2 + "queries->popQuery(topQuery);", 1),
    (CG, "queries->popQuery(garrisonQuery);",
     T * 2 + 'fprintf(stderr, "[ML-stk] caller=CG-garrisonAnswer\\n");\n' + T * 2 + "queries->popQuery(garrisonQuery);", 1),
    (CG, "queries->popIfTop(visitQuery); //visit ends here if no queries were created",
     T * 2 + 'fprintf(stderr, "[ML-stk] caller=CG-objectVisitedTail\\n");\n'
     + T * 2 + "queries->popIfTop(visitQuery); //visit ends here if no queries were created", 1),
    (CG, "queries->popIfTop(moveQuery);",
     T * 2 + 'fprintf(stderr, "[ML-stk] caller=CG-moveHeroTail\\n");\n' + T * 2 + "queries->popIfTop(moveQuery);", 1),
    (BR, "gameHandler->queries->popIfTop(battleQuery); // Workaround",
     T * 2 + 'fprintf(stderr, "[ML-stk] caller=BR-battleResultAIcase\\n");\n'
     + T * 2 + "gameHandler->queries->popIfTop(battleQuery); // Workaround", 1),
]


def main():
    if "rollback" in sys.argv:
        for f in (QP, CG, BR):
            bak = f + ".bak_stk298"
            if os.path.exists(bak):
                shutil.copy2(bak, f)
                print("[OK] 回退 %s" % f)
            else:
                print("[SKIP] 无备份 %s" % bak)
        return

    contents = {}
    for f in (QP, CG, BR):
        with open(f, "r", encoding="utf-8") as fh:
            contents[f] = fh.read()
    if any("[ML-stk]" in c for c in contents.values()):
        print("[SKIP] 插桩已存在, 幂等退出")
        return

    bad = 0
    for f, anchor, _new, expect in EDITS:
        n = contents[f].count(anchor)
        if n != expect:
            print("[FAIL] %s 锚点命中 %d (期望 %d): %r" % (f, n, expect, anchor[:70]))
            bad += 1
    if bad:
        print("[FAIL] %d 处锚点不匹配, 未写入任何文件" % bad)
        sys.exit(1)
    print("[OK] 锚点全量校验通过 (%d 处)" % len(EDITS))

    for f in (QP, CG, BR):
        shutil.copy2(f, f + ".bak_stk298")
    for f, anchor, new, _e in EDITS:
        contents[f] = contents[f].replace(anchor, new, 1)
    for f in (QP, CG, BR):
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(contents[f])
    print("[OK] 插桩写入 %d 处 (备份 .bak_stk298)" % len(EDITS))


if __name__ == "__main__":
    main()
