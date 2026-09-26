#!/usr/bin/env python3
"""取兵链路修复 v2 (09-27): case16-18 盲 moveHero → case24 完整范式 (近进城/远走格)

v1 (892343da 移植) 缺陷: 非邻接时 cb->moveHero 被引擎拒 ("Tiles ... not neighboring"),
T06 duel 英雄开局距城 3 格 → 窗内招兵拍全 no-op (引擎 ERROR 刷屏实锤)。
v2: distSq(standPos, cur->pos)<=2 → moveHero 进城; 否则 moveOneStepToward 走一格逼近
(与 case24 MOVE_TO 同款; H3M 邻接图行为不变; case22 同款缺陷不修 — runner 已 mask 该动作)。

用法: python3 patch_recruit_fix_wsl_v2.py [--rollback]
"""
import sys
import os
import shutil

TARGET = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
BAK = TARGET + ".bak_recruitfix_v1_0927"

OLD = "\t\t\tcb->moveHero(cur, standPos, false);\n"

NEW = """\t\t\t// 09-27 v2: 盲目 moveHero 只在相邻格有效 (引擎拒非邻接: "Tiles ... not neighboring")
\t\t\t// — T06 duel 英雄开局距城 3 格, 窗内拍全被拒 → 招兵 no-op (引擎 ERROR 刷屏实锤)。
\t\t\t// 改 case24 完整范式: 近 (distSq<=2) moveHero 进城; 远则本拍走一格逼近
\t\t\t// (招兵拍降级为走格; 窗 4 拍 = 走 2-3 格 + 进城招 1-2 拍, H3M 邻接图行为不变)。
\t\t\tif (distSq(standPos, cur->pos) <= 2)
\t\t\t\tcb->moveHero(cur, standPos, false);
\t\t\telse
\t\t\t\tmoveOneStepToward(cb, cur, standPos);
"""


def main():
    rollback = "--rollback" in sys.argv
    if rollback:
        if not os.path.exists(BAK):
            print(f"回滚失败: 无备份 {BAK}")
            return 1
        shutil.copy2(BAK, TARGET)
        print(f"已回滚 v2: {BAK} → {TARGET} (回到 v1 状态)")
        return 0

    src = open(TARGET, encoding="utf-8").read()
    if "09-27 v2" in src:
        print("v2 已应用 (幂等跳过)")
        return 0
    cnt = src.count(OLD)
    if cnt < 1:
        print(f"锚点异常: moveHero 行出现 {cnt} 次, 终止")
        return 1
    # 首次出现 = case16-18 的修复块 (L25x, 早于 case22 L32x)
    shutil.copy2(TARGET, BAK)
    out = src.replace(OLD, NEW, 1)
    open(TARGET, "w", encoding="utf-8", newline="").write(out)
    chk = open(TARGET, encoding="utf-8").read()
    ok = ("09-27 v2" in chk) and ("distSq(standPos, cur->pos) <= 2" in chk)
    # 验证 case22 的盲 moveHero 未被误改 (应仍有一处未带 v2 注释的裸 moveHero 行)
    bare = chk.count("\t\t\tcb->moveHero(cur, standPos, false);\n")
    print(f"应用完成, 验证: {'PASS' if ok else 'FAIL'}  (case22 裸 moveHero 残留 {bare} 处, 期望 1)")
    if not ok:
        shutil.copy2(BAK, TARGET)
        print("验证失败, 已回滚")
        return 1
    print(f"备份: {BAK}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
