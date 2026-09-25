#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#298 UpgradeCreature 死循环: 打点 + 熔断 (09-23)

打点: CClient::sendRequest 里对 UpgradeCreature 包打印 waitTillRealize / onNetworkThread
      → 判定"客户端是否没等确认"(状态分歧假设)
熔断: AIGateway::makePossibleUpgrades 的 do-while 加 8 次上限 + BREAK 打点
      → 止血, 防止 2.4GB 刷屏

运行: wsl -u root bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/patch_298_upgrade_probe.py"
回退: 同命令加 rollback
"""
import os
import shutil
import sys

BASE = os.environ.get("BASE", "/home/administrator/vcmi-native")
CC = BASE + "/client/Client.cpp"
AG = BASE + "/AI/Nullkiller2/AIGateway.cpp"
T = "\t"
MARK = "[ML-upg]"

PROBE = (
    T + 'if(std::string(typeid(request).name()).find("UpgradeCreature") != std::string::npos)\n'
    + T * 2 + 'fprintf(stderr, "[ML-upg] UpgradeCreature req=%d waitTillRealize=%d onNetThread=%d\\n", '
    + "requestID, (int)waitTillRealize, (int)CClient::onNetworkThread);\n"
)

OLD_LOOP_HEAD = (
    T * 3 + "do\n"
    + T * 3 + "{\n"
    + T * 4 + "cc->fillUpgradeInfo(obj, SlotID(i), upgradeInfo);\n"
)

NEW_LOOP_HEAD = (
    T * 3 + "int _mlUpgLoop = 0; // ML probe/circuit-breaker (09-23, #298)\n"
    + T * 3 + "do\n"
    + T * 3 + "{\n"
    + T * 4 + "cc->fillUpgradeInfo(obj, SlotID(i), upgradeInfo);\n"
    + T * 4 + "++_mlUpgLoop;\n"
    + T * 4 + 'if(_mlUpgLoop <= 10) fprintf(stderr, "[ML-upg] loop slot=%d n=%d hasUpgrades=%d\\n", i, _mlUpgLoop, (int)upgradeInfo.hasUpgrades());\n'
)

OLD_LOOP_TAIL = (
    T * 3 + "}\n"
    + T * 3 + "while(upgradeInfo.hasUpgrades());\n"
)

NEW_LOOP_TAIL = (
    T * 3 + "}\n"
    + T * 3 + "while(_mlUpgLoop < 8 && upgradeInfo.hasUpgrades());\n"
    + T * 3 + 'if(_mlUpgLoop >= 8) fprintf(stderr, "[ML-upg] BREAK slot=%d n=%d (client/server upgrade state divergence)\\n", i, _mlUpgLoop);\n'
)

EDITS = [
    (CC, T + "ui32 requestID = requestCounter++;\n",
     T + "ui32 requestID = requestCounter++;\n" + PROBE, 1),
    (AG, OLD_LOOP_HEAD, NEW_LOOP_HEAD, 1),
    (AG, OLD_LOOP_TAIL, NEW_LOOP_TAIL, 1),
]
FILES = [CC, AG]


def main():
    if "rollback" in sys.argv:
        for f in FILES:
            bak = f + ".bak_upg298"
            if os.path.exists(bak):
                shutil.copy2(bak, f)
                print("[OK] 回退 %s" % f)
            else:
                print("[SKIP] 无备份 %s" % bak)
        return

    contents = {}
    for f in FILES:
        with open(f, "r", encoding="utf-8") as fh:
            contents[f] = fh.read()
    if any(MARK in c for c in contents.values()):
        print("[SKIP] 打点已存在, 幂等退出")
        return

    bad = 0
    for f, anchor, _new, expect in EDITS:
        n = contents[f].count(anchor)
        if n != expect:
            print("[FAIL] %s 锚点命中 %d (期望 %d): %r" % (f, n, expect, anchor[:70]))
            bad += 1
    if bad:
        print("[FAIL] %d 处锚点不匹配, 未写入" % bad)
        sys.exit(1)
    print("[OK] 锚点校验通过 (%d 处)" % len(EDITS))

    for f in FILES:
        shutil.copy2(f, f + ".bak_upg298")
    for f, anchor, new, _e in EDITS:
        contents[f] = contents[f].replace(anchor, new, 1)
    for f in FILES:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(contents[f])
    print("[OK] 打点+熔断写入 %d 处 (备份 .bak_upg298)" % len(EDITS))


if __name__ == "__main__":
    main()
