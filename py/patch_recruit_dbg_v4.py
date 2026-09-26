#!/usr/bin/env python3
"""取兵链路诊断 v4 (09-27): case16-18 加 fprintf 打印 visiting 态 + 每级可招数量
用途: 一次性诊断 (RECRUITED=0 最后歧义: 英雄是否 visiting / available 是否 day-1=0)
用法: python3 patch_recruit_dbg_v4.py [--rollback]
"""
import sys
import os
import shutil

TARGET = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
BAK = TARGET + ".bak_recruitfix_v3_0927"

ANCHOR = """\t\t// 英雄已 visiting 本城: 引擎校验 CGameHandler::recruitCreatures L2463 接受
\t\t// dst ∈ {town, garrisonHero, visitingHero}。dst=cur (执行英雄=visiting hero) → 兵直上
\t\t// 英雄部队 (py [RECRUITED] 实测口径 = 英雄 army power 增量)。
\t\t// ⚠ 不能退回 town->getUpperArmy(): 它只在英雄 garrison(驻守)时返回英雄,
\t\t//   visiting(进城访问)时返回城本身 → 兵落城 garrison, 英雄部队恒 0 (本 bug 根因)。
\t\tconst CArmedInstance * dst = cur;
"""

NEW = """\t\t// 英雄已 visiting 本城: 引擎校验 CGameHandler::recruitCreatures L2463 接受
\t\t// dst ∈ {town, garrisonHero, visitingHero}。dst=cur (执行英雄=visiting hero) → 兵直上
\t\t// 英雄部队 (py [RECRUITED] 实测口径 = 英雄 army power 增量)。
\t\t// ⚠ 不能退回 town->getUpperArmy(): 它只在英雄 garrison(驻守)时返回英雄,
\t\t//   visiting(进城访问)时返回城本身 → 兵落城 garrison, 英雄部队恒 0 (本 bug 根因)。
\t\tconst CArmedInstance * dst = cur;
\t\tfprintf(stderr, "[RECDBG] a=%d hero=(%d,%d) visiting=%d townAvail=", a, cur->pos.x, cur->pos.y,
\t\t\tcur->getVisitedTown() == town ? 1 : 0);
\t\tfor (size_t lv = 0; lv < creatures.size() && lv < 7; lv++)
\t\t\tfprintf(stderr, "[L%zu:%d/%zu]", lv, creatures[lv].first, creatures[lv].second.size());
\t\tfprintf(stderr, "\\n");
"""


def main():
    rollback = "--rollback" in sys.argv
    if rollback:
        if not os.path.exists(BAK):
            print(f"回滚失败: 无备份 {BAK}")
            return 1
        shutil.copy2(BAK, TARGET)
        print("已回滚 v4 (回到 v3 状态)")
        return 0

    src = open(TARGET, encoding="utf-8").read()
    if "[RECDBG]" in src:
        print("v4 已应用 (幂等跳过)")
        return 0
    if src.count(ANCHOR) != 1:
        print(f"锚点异常: {src.count(ANCHOR)}")
        return 1
    shutil.copy2(TARGET, BAK)
    out = src.replace(ANCHOR, NEW, 1)
    open(TARGET, "w", encoding="utf-8", newline="").write(out)
    chk = open(TARGET, encoding="utf-8").read()
    ok = chk.count("[RECDBG]") >= 2
    print(f"应用完成: {'PASS' if ok else 'FAIL'}  备份: {BAK}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
