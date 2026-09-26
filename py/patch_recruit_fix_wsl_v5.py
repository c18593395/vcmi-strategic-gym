#!/usr/bin/env python3
"""取兵链路修复 v5 (09-27): 放弃 visiting 路线, garrison 中转 + mergeStacks 并入英雄

v1-v4 全卡死在同一处: case16-18 依赖 town->visitablePos() 几何 — T06 duel 城 (2,2) 实测
visitable=(0,2) (x=0 图边缘外), 英雄永远无法进入 visiting 态 (v4c RECDBG 全 0 实锤)。
v5 零几何: ① dst=town 招进 garrison (引擎 dst 三选一恒合法) ② mergeStacks 全量并入英雄
(showGarrisonDialog 08-27 修复同款原语)。T06 城 garrison 初始空 (obs 全 0), 快照对比只搬
本次新增, 无副作用; H3M 图 (judgement_day) 亦无需 visiting, 行为更稳。

用法: python3 patch_recruit_fix_wsl_v5.py [--rollback]
"""
import sys
import os
import shutil

TARGET = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
BAK = TARGET + ".bak_recruitfix_v4_0927"

OLD = """\t\t{
\t\t\tint3 vtp = town->visitablePos();
\t\t\tint3 vsp = cur->convertFromVisitablePos(vtp);
\t\t\tfprintf(stderr, "[RECDBG] a=%d hero=(%d,%d) visitedTown=%d town=(%d,%d) visitable=(%d,%d) stand=(%d,%d)\\n",
\t\t\t\ta, cur->pos.x, cur->pos.y, cur->getVisitedTown() ? 1 : 0,
\t\t\t\ttown->pos.x, town->pos.y, vtp.x, vtp.y, vsp.x, vsp.y);
\t\t}
\t\t// 09-25 取兵链路根因修复: dst=town->getUpperArmy() 只在英雄 "驻守/visiting" 本城时
\t\t// 返回英雄, 否则返回城本身 → 兵全落城 garrison, 英雄部队恒 0, py 侧 [RECRUITED]
\t\t// (英雄部队 power 增量) 结构性恒 0 (94 次 RECRUIT 实锤 0/16 局涨幅)。
\t\t// 修法 = 复用 case 22 同款进城范式 (moveHero→visitablePos 触发进城, query 自动应答,
\t\t// 锁内等待 getVisitedTown 生效); 引擎校验 CGameHandler::recruitCreatures L2463:
\t\t// dst 须 = town / garrisonHero / visitingHero 三者之一 → 进城后 dst=英雄 合法。
\t\t// 单英雄 1v1 场景无 garrison 敌将, moveHero 进城无副作用 (英雄原地驻守, 下回合照常动)。
\t\tif (!cur->getVisitedTown() || cur->getVisitedTown() != town)
\t\t{
\t\t\tint3 tp = town->visitablePos();
\t\t\tint3 standPos = cur->convertFromVisitablePos(tp);
\t\t\t// 09-27 v2: 盲目 moveHero 只在相邻格有效 (引擎拒非邻接: "Tiles ... not neighboring")
\t\t\t// — T06 duel 英雄开局距城 3 格, 窗内拍全被拒 → 招兵 no-op (引擎 ERROR 刷屏实锤)。
\t\t\t// 改 case24 完整范式: 近 (distSq<=2) moveHero 进城; 远则本拍走一格逼近
\t\t\t// (招兵拍降级为走格; 窗 4 拍 = 走 2-3 格 + 进城招 1-2 拍, H3M 邻接图行为不变)。
\t\t\tif (distSq(standPos, cur->pos) <= 2)
\t\t\t\tcb->moveHero(cur, standPos, false);
\t\t\telse
\t\t\t\tmoveTowardFallback(cb, cur, standPos);
\t\t\t// 锁内等 2s 让进城完成 (query 自动应答, 同 case 22)
\t\t\tfor (int i = 0; i < 20; i++) {
\t\t\t\tstd::this_thread::sleep_for(std::chrono::milliseconds(100));
\t\t\t\tif (cur->getVisitedTown() == town)
\t\t\t\t\tbreak;
\t\t\t}
\t\t\tif (!cur->getVisitedTown())
\t\t\t\treturn noTarget;  // 仍未进城, 放弃 (本拍 no-op, 不扣资源)
\t\t}
\t\t// 英雄已 visiting 本城: 引擎校验 CGameHandler::recruitCreatures L2463 接受
\t\t// dst ∈ {town, garrisonHero, visitingHero}。dst=cur (执行英雄=visiting hero) → 兵直上
\t\t// 英雄部队 (py [RECRUITED] 实测口径 = 英雄 army power 增量)。
\t\t// ⚠ 不能退回 town->getUpperArmy(): 它只在英雄 garrison(驻守)时返回英雄,
\t\t//   visiting(进城访问)时返回城本身 → 兵落城 garrison, 英雄部队恒 0 (本 bug 根因)。
\t\tconst CArmedInstance * dst = cur;
\t\tconst auto & creatures = town->creatures; // creatures[level(0-based)] -> {count, {base, upgrades}}
"""

NEW = """\t\t// 09-27 v5: 放弃 visiting 路线 — visitablePos 依赖几何 (T06 duel 城 (2,2) 实测
\t\t// visitable=(0,2) 图边缘外, 英雄永远进不了 visiting 态, v1-v4 全被此卡死)。
\t\t// 零几何方案: ① dst=town 招进 garrison (引擎 dst 三选一恒合法)
\t\t// ② mergeStacks 把本次新增 garrison 全量并入英雄部队 (showGarrisonDialog 08-27 同款原语)。
\t\t// T06 城 garrison 初始为空 (obs 全 0), 快照对比只搬新增, 无副作用。
\t\tconst CArmedInstance * dst = town;
\t\tconst auto & creatures = town->creatures; // creatures[level(0-based)] -> {count, {base, upgrades}}
\t\tfprintf(stderr, "[RECDBG] a=%d hero=(%d,%d) avail=", a, cur->pos.x, cur->pos.y);
\t\tfor (size_t lv = 0; lv < creatures.size() && lv < 7; lv++)
\t\t\tfprintf(stderr, "[L%zu:%d/%zu]", lv, creatures[lv].first, creatures[lv].second.size());
\t\tfprintf(stderr, "\\n");
\t\t// garrison 快照 (搬新增用)
\t\tstd::vector<std::pair<SlotID, int>> garBefore;
\t\tfor (const auto & [slot, stack] : town->Slots())
\t\t\tif (stack && stack->getCount() > 0)
\t\t\t\tgarBefore.push_back({slot, stack->getCount()});
"""


def main():
    rollback = "--rollback" in sys.argv
    if rollback:
        if not os.path.exists(BAK):
            print(f"回滚失败: 无备份 {BAK}")
            return 1
        shutil.copy2(BAK, TARGET)
        print("已回滚 v5 (回到 v4 状态)")
        return 0

    src = open(TARGET, encoding="utf-8").read()
    if "v5: 放弃 visiting 路线" in src:
        print("v5 已应用 (幂等跳过)")
        return 0
    if src.count(OLD) != 1:
        print(f"锚点异常: {src.count(OLD)}")
        return 1
    shutil.copy2(TARGET, BAK)

    # 在两处 recruitCreatures 加 first>0 guard
    src = src.replace(OLD, NEW, 1)
    src = src.replace(
        "\t\t\t\tif (!creatures[i].second.empty())\n\t\t\t\t{\n\t\t\t\t\tcb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);\n\t\t\t\t\tbreak;\n\t\t\t\t}",
        "\t\t\t\tif (!creatures[i].second.empty() && creatures[i].first > 0)\n\t\t\t\t{\n\t\t\t\t\tcb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);\n\t\t\t\t\tbreak;\n\t\t\t\t}",
        1,
    )
    src = src.replace(
        "\t\t\t\tif (!creatures[i].second.empty())\n\t\t\t\t\tcb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);",
        "\t\t\t\tif (!creatures[i].second.empty() && creatures[i].first > 0)\n\t\t\t\t\tcb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);",
        1,
    )

    # 在 break; 前插 merge 块 (case16-18 尾部, case 19 之前的那个 break)
    MERGE_ANCHOR = """\t\t\t\tif (!creatures[i].second.empty() && creatures[i].first > 0)
\t\t\t\t\tcb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);
\t\t\t}
\t\t}
\t\tbreak;
\t}"""
    MERGE_NEW = """\t\t\t\tif (!creatures[i].second.empty() && creatures[i].first > 0)
\t\t\t\t\tcb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);
\t\t\t}
\t\t}
\t\t// garrison → 英雄: 只搬本次新增 (快照对比), 全部并入英雄部队
\t\tfor (const auto & [slot, stack] : town->Slots())
\t\t{
\t\t\tif (!stack || stack->getCount() <= 0) continue;
\t\t\tint beforeCnt = 0;
\t\t\tfor (const auto & [bs, bc] : garBefore)
\t\t\t\tif (bs == slot) { beforeCnt = bc; break; }
\t\t\tif (stack->getCount() <= beforeCnt) continue;
\t\t\ttry {
\t\t\t\tSlotID dslot = cur->getSlotFor(stack->getCreature());
\t\t\t\tif (!dslot.validSlot())
\t\t\t\t\tdslot = cur->getFreeSlot();
\t\t\t\tif (dslot.validSlot())
\t\t\t\t\tcb->mergeStacks(town, cur, slot, dslot);
\t\t\t} catch(...) {}
\t\t}
\t\tbreak;
\t}"""
    assert src.count(MERGE_ANCHOR) == 1, f"merge 锚点 {src.count(MERGE_ANCHOR)}"
    src = src.replace(MERGE_ANCHOR, MERGE_NEW, 1)

    open(TARGET, "w", encoding="utf-8", newline="").write(src)
    chk = open(TARGET, encoding="utf-8").read()
    ok = ("v5: 放弃 visiting" in chk) and ("mergeStacks(town, cur, slot, dslot)" in chk) and ("moveTowardFallback(cb, cur, standPos)" not in chk.split("case 19:")[0].split("case 16:")[1])
    print(f"应用完成: {'PASS' if ok else 'FAIL'}  备份: {BAK}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
