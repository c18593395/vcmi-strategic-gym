#!/usr/bin/env python3
"""取兵链路修复 v6 (09-27): garrison→hero 合并挪到拍首 (异步应用一拍延迟的对策)

用法: python3 patch_recruit_fix_wsl_v6.py [--rollback]
"""
import sys
import os
import shutil

TARGET = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
BAK = TARGET + ".bak_recruitfix_v5_0927"

OLD_TAIL = """\t\t// garrison 快照 (搬新增用)
\t\tstd::vector<std::pair<SlotID, int>> garBefore;
\t\tfor (const auto & [slot, stack] : town->Slots())
\t\t\tif (stack && stack->getCount() > 0)
\t\t\t\tgarBefore.push_back({slot, stack->getCount()});
"""
OLD_TAIL2 = """\t\t// garrison → 英雄: 只搬本次新增 (快照对比), 全部并入英雄部队
\t\tfor (const auto & [slot, stack] : town->Slots())
\t\t{
\t\t\tif (!stack || stack->getCount() <= 0) continue;
\t\t\tint beforeCnt = 0;
\t\t\tfor (const auto & [bs, bc] : garBefore)
\t\t\t\tif (bs == slot) { beforeCnt = bc; break; }
\t\t\tif (stack->getCount() <= beforeCnt) continue;
\t\t\tSlotID dslot = cur->getSlotFor(stack->getCreature());
\t\t\tif (!dslot.validSlot())
\t\t\t\tdslot = cur->getFreeSlot();
\t\t\tfprintf(stderr, "[MERGEDBG] slot=%d cnt=%d dslot=%d visiting=%d\\n",
\t\t\t\tslot.getNum(), stack->getCount(), dslot.validSlot() ? dslot.getNum() : -1,
\t\t\t\tcur->getVisitedTown() ? 1 : 0);
\t\t\ttry {
\t\t\t\tif (dslot.validSlot())
\t\t\t\t\tcb->mergeStacks(town, cur, slot, dslot);
\t\t\t} catch(...) { fprintf(stderr, "[MERGEDBG] exception\\n"); }
\t\t}
"""

MERGE_AT_ENTRY = """\t\tfprintf(stderr, "[L%zu:%d/%zu]", lv, creatures[lv].first, creatures[lv].second.size());
\t\tfprintf(stderr, "\\n");
\t\t// 09-27 v6: garrison→hero 合并在拍首 — 上一拍 recruit 此刻已应用 (sendRequest 异步
\t\t// 一拍延迟), 此处 garrison 可见; 城上出生 → visiting 常在 → 交换位满足 → 兵直上英雄。
\t\tfor (const auto & [slot, stack] : town->Slots())
\t\t{
\t\t\tif (!stack || stack->getCount() <= 0) continue;
\t\t\tSlotID dslot = cur->getSlotFor(stack->getCreature());
\t\t\tif (!dslot.validSlot())
\t\t\t\tdslot = cur->getFreeSlot();
\t\t\tfprintf(stderr, "[MERGEDBG] slot=%d cnt=%d dslot=%d visiting=%d\\n",
\t\t\t\tslot.getNum(), stack->getCount(), dslot.validSlot() ? dslot.getNum() : -1,
\t\t\t\tcur->getVisitedTown() ? 1 : 0);
\t\t\ttry {
\t\t\t\tif (dslot.validSlot())
\t\t\t\t\tcb->mergeStacks(town, cur, slot, dslot);
\t\t\t} catch(...) { fprintf(stderr, "[MERGEDBG] exception\\n"); }
\t\t}
"""

HEAD_ANCHOR = """\t\tfprintf(stderr, "[L%zu:%d/%zu]", lv, creatures[lv].first, creatures[lv].second.size());
\t\tfprintf(stderr, "\\n");
"""


def main():
    rollback = "--rollback" in sys.argv
    if rollback:
        if not os.path.exists(BAK):
            print(f"回滚失败: 无备份 {BAK}")
            return 1
        shutil.copy2(BAK, TARGET)
        print("已回滚 v6 (回到 v5b 状态)")
        return 0

    src = open(TARGET, encoding="utf-8").read()
    if "v6: garrison→hero 合并在拍首" in src:
        print("v6 已应用 (幂等跳过)")
        return 0
    assert src.count(OLD_TAIL) == 1, f"快照锚点 {src.count(OLD_TAIL)}"
    assert src.count(OLD_TAIL2) == 1, f"拍尾锚点 {src.count(OLD_TAIL2)}"
    assert src.count(HEAD_ANCHOR) == 1, f"HEAD 锚点 {src.count(HEAD_ANCHOR)}"
    shutil.copy2(TARGET, BAK)
    src = src.replace(OLD_TAIL, "", 1)
    src = src.replace(OLD_TAIL2, "", 1)
    src = src.replace(HEAD_ANCHOR, MERGE_AT_ENTRY, 1)
    open(TARGET, "w", encoding="utf-8", newline="").write(src)
    chk = open(TARGET, encoding="utf-8").read()
    ok = ("v6: garrison→hero 合并在拍首" in chk) and ("garBefore" not in chk) and (chk.count("[MERGEDBG]") == 2)
    print(f"应用完成: {'PASS' if ok else 'FAIL'}  备份: {BAK}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
