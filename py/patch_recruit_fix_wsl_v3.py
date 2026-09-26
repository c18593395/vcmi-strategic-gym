#!/usr/bin/env python3
"""取兵链路修复 v3 (09-27): case16-18 走格加多方向回退

v2 缺陷: moveOneStepToward 贪心单方向 (最大点积) 无回退 — 从 (3,3) 望向 standPos(1,2)
最大点积方向 = NW = (2,2) 城格 (阻挡) → moveHero 每拍被拒 → 英雄冻结 (pos 全窗不变实锤)。
v3: 新增 moveTowardFallback (8 方向按点积降序逐试, pos 变化验证成功); 次选 W=(2,3)
恰为城 visitable 格 → 走上即触发 town visit → 同拍 wait 循环检测 → 招兵直上英雄。

用法: python3 patch_recruit_fix_wsl_v3.py [--rollback]
"""
import sys
import os
import shutil

TARGET = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
BAK = TARGET + ".bak_recruitfix_v2_0927"

# 锚点: moveOneStepToward 函数结尾 (在它后面插入新助手; 实测函数体 1-tab 缩进)
HELPER_ANCHOR = """\ttry {
\t\tint3 targetPos(hero->pos.x + ddx[bestDir], hero->pos.y + ddy[bestDir], hero->pos.z);
\t\tcb->moveHero(hero, targetPos, false);
\t\treturn true;
\t} catch(...) { return false; }
}
"""

HELPER_NEW = """\ttry {
\t\tint3 targetPos(hero->pos.x + ddx[bestDir], hero->pos.y + ddy[bestDir], hero->pos.z);
\t\tcb->moveHero(hero, targetPos, false);
\t\treturn true;
\t} catch(...) { return false; }
}

// 09-27 v3: 多方向回退走格 — 贪心单方向会被目标途中阻挡格卡死 (城格 NW 挡路实锤:
// (3,3)→standPos(1,2) 最大点积=NW=(2,2) 城格, 每拍被拒 → 英雄整窗冻结)。
// 8 方向按与 (dx,dy) 点积降序逐试, 以 hero->pos 实际变化判定成功; 走上城 visitable 格
// 会自动触发 town visit (招兵窗前置态), 正合 case16-18 用途。
bool moveTowardFallback(CCallback * cb, const CGHeroInstance * hero, const int3 & target)
{
\tif (!cb || !hero) return false;
\tint dx = target.x - hero->pos.x;
\tint dy = target.y - hero->pos.y;
\tif (dx == 0 && dy == 0) return false;
\tstatic const int ddx[8] = {0, 1, 1, 1, 0, -1, -1, -1};
\tstatic const int ddy[8] = {-1, -1, 0, 1, 1, 1, 0, -1};
\tint order[8];
\tint64_t dots[8];
\tfor (int d = 0; d < 8; d++) {
\t\tdots[d] = (int64_t)dx * ddx[d] + (int64_t)dy * ddy[d];
\t\torder[d] = d;
\t}
\t// 简单插入排序 (8 元素): 点积降序
\tfor (int i = 1; i < 8; i++) {
\t\tint oi = order[i]; int64_t di = dots[i];
\t\tint j = i - 1;
\t\twhile (j >= 0 && dots[order[j]] < di) { order[j + 1] = order[j]; j--; }
\t\torder[j + 1] = oi;
\t}
\tconst int3 before = hero->pos;
\tfor (int i = 0; i < 8; i++) {
\t\tif (dots[order[i]] <= 0) break;  // 只试前进/侧向, 不往回走
\t\tint3 cand(hero->pos.x + ddx[order[i]], hero->pos.y + ddy[order[i]], hero->pos.z);
\t\ttry { cb->moveHero(hero, cand, false); } catch(...) { continue; }
\t\tif (hero->pos != before)
\t\t\treturn true;  // 实际位移成功 (可能已触发城 visit)
\t}
\treturn false;
}
"""

# 锚点: case16-18 里的 v2 走格调用 → 换 fallback
CALL_OLD = "\t\t\t\tmoveOneStepToward(cb, cur, standPos);\n"
CALL_NEW = "\t\t\t\tmoveTowardFallback(cb, cur, standPos);\n"


def main():
    rollback = "--rollback" in sys.argv
    if rollback:
        if not os.path.exists(BAK):
            print(f"回滚失败: 无备份 {BAK}")
            return 1
        shutil.copy2(BAK, TARGET)
        print(f"已回滚 v3 (回到 v2 状态)")
        return 0

    src = open(TARGET, encoding="utf-8").read()
    if "moveTowardFallback" in src:
        print("v3 已应用 (幂等跳过)")
        return 0
    if src.count(HELPER_ANCHOR) != 1 or src.count(CALL_OLD) < 1:
        print(f"锚点异常: helper={src.count(HELPER_ANCHOR)} call={src.count(CALL_OLD)}")
        return 1
    shutil.copy2(TARGET, BAK)
    out = src.replace(HELPER_ANCHOR, HELPER_NEW, 1)
    # CALL_OLD 首次出现 = case16-18 (v2 块在 case22 之前)
    out = out.replace(CALL_OLD, CALL_NEW, 1)
    open(TARGET, "w", encoding="utf-8", newline="").write(out)
    chk = open(TARGET, encoding="utf-8").read()
    ok = (chk.count("moveTowardFallback") == 2) and (CALL_NEW in chk)
    print(f"应用完成, 验证: {'PASS' if ok else 'FAIL'}")
    if not ok:
        shutil.copy2(BAK, TARGET)
        print("验证失败, 已回滚")
        return 1
    print(f"备份: {BAK}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
