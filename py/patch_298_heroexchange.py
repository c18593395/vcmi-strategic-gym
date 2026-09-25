#!/usr/bin/env python3
"""#298 S 精准修复: CGameHandler::heroExchange 加 AI 间自动关闭 (09-23)
对齐 makeGarrisonDialog 08-27 bothAI 同款模式。精确替换 + count 断言 + 自动备份, 失败即退。
运行: wsl bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/patch_298_heroexchange.py"
"""
import os
import shutil, sys

TARGET = os.environ.get("TARGET", "/home/administrator/vcmi-native/server/CGameHandler.cpp")
BACKUP = TARGET + ".bak_298_0923"

ANCHOR = "\t\tauto exchange = std::make_shared<CGarrisonDialogQuery>(this, h1, h2);"
INSERT = """\t\t// ML fix (09-23, #298): AI 间英雄相遇不弹 ExchangeDialog 不建查询 (对齐
\t\t// makeGarrisonDialog 08-27 bothAI 同款模式)。NK2 应答走 executeActionAsync 异步
\t\t// (AIGateway.cpp:263), 主循环卡住时 answerQuery 永不下发 → Exchange 查询 q=1 恒挂
\t\t// → 蓝方回合不推进 → adventure_wait 300s 强停 → traj=None 静默吞局 (h3m 池 batch1
\t\t// 三图 100+ 局零出现根因, py/_298_repro.sh 停训窗 5 局取证 4/4 全挂含 viking 对照)。
\t\t// AI 间军队/宝物合并放弃 (NK2 pickBestCreatures 不执行, 训练语义影响小);
\t\t// 学者技能交换保留 (官方: "Visits can still be useful ... Scholar")。
\t\tconst auto * exP1 = gameInfo().getPlayerState(h1->getOwner());
\t\tconst auto * exP2 = gameInfo().getPlayerState(h2->getOwner());
\t\tbool bothAI = exP1 && !exP1->isHuman() && exP2 && !exP2->isHuman();
\t\tif (bothAI)
\t\t{
\t\t\tuseScholarSkill(hero1,hero2);
\t\t\treturn;
\t\t}

"""

def main():
    with open(TARGET, "r", encoding="utf-8") as f:
        content = f.read()

    n = content.count(ANCHOR)
    if n != 1:
        print(f"[FAIL] 锚点命中 {n} 次 (期望 1), 不写入。源码可能已变动或已打过补丁。")
        if "ML fix (09-23, #298)" in content:
            print("[SKIP] 检测到补丁已存在, 幂等退出")
            return
        sys.exit(1)

    if "#298" in content and "heroExchange" in content and "ML fix (09-23" in content:
        print("[SKIP] 补丁已存在")
        return

    shutil.copy2(TARGET, BACKUP)
    print(f"[OK] 备份 → {BACKUP}")

    patched = content.replace(ANCHOR, INSERT + ANCHOR)
    if patched.count("ML fix (09-23, #298)") != 1:
        print("[FAIL] 替换后校验失败, 不写入")
        sys.exit(1)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(patched)
    print("[OK] patch 写入完成: heroExchange bothAI 自动关闭 (保留 useScholarSkill)")

if __name__ == "__main__":
    main()
