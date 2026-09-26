#!/usr/bin/env python3
"""WSL 取兵链路修复移植 (892343da hunk1: case16-18 dst=getUpperArmy→dst=cur)
只移植缺失的 hunk1; hunk2(5参 showGarrisonDialog)/hunk3(onNewSystemMessageReceived) WSL 已有, 跳过。
模式: 备份(.bak_recruitfix_0927 已有, 幂等重建) + 锚点唯一性校验 + 精确替换 + 验证 + 回滚支持。

用法: python3 patch_recruit_fix_wsl.py            # 应用
      python3 patch_recruit_fix_wsl.py --rollback # 回滚
"""
import sys, os, shutil

TARGET = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
BAK = TARGET + ".bak_recruitfix_0927"

OLD = "\t\tconst CArmedInstance * dst = town->getUpperArmy();\n"

NEW = """\t\t// 09-25 取兵链路根因修复: dst=town->getUpperArmy() 只在英雄 "驻守/visiting" 本城时
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
\t\t\tcb->moveHero(cur, standPos, false);
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
"""


def main():
    rollback = "--rollback" in sys.argv
    if rollback:
        if not os.path.exists(BAK):
            print(f"回滚失败: 无备份 {BAK}"); return 1
        shutil.copy2(BAK, TARGET)
        print(f"已回滚: {BAK} → {TARGET}")
        return 0

    src = open(TARGET, encoding="utf-8").read()
    cnt = src.count(OLD)
    if "dst = cur;" in src and "取兵链路根因修复" in src:
        print("已应用过 (幂等跳过)"); return 0
    if cnt != 1:
        print(f"锚点异常: getUpperArmy dst 行出现 {cnt} 次 (期望 1), 终止"); return 1
    # 备份
    shutil.copy2(TARGET, BAK)
    out = src.replace(OLD, NEW, 1)
    open(TARGET, "w", encoding="utf-8", newline="").write(out)
    # 验证
    chk = open(TARGET, encoding="utf-8").read()
    ok = ("dst = cur;" in chk) and ("取兵链路根因修复" in chk) and ("getVisitedTown() != town" in chk)
    print("应用完成, 验证:", "PASS" if ok else "FAIL")
    if not ok:
        shutil.copy2(BAK, TARGET); print("验证失败, 已回滚"); return 1
    print(f"备份: {BAK}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
