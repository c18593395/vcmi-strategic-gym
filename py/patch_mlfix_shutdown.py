#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ML fix: SHUTDOWN 延迟到当前包处理完 (09-24, Mode A 冻结根因, gdb 断点实锤)。

上游缺陷: 胜负判定发生在包处理中途 (moveHero → 占城 → onTownCaptured → setOwner
→ checkVictoryLossConditionsForPlayer:3854), 该路径直接 setState(SHUTDOWN)
→ networkHandler->stop() 立即杀掉网络循环 → 当前包流被截断
(PackageApplied/胜利包不再发送, 已入队请求不再处理) → 客户端 AI sendRequest
永久等 realize → 游戏冻结 (rc=124)。
实证: gdb 断点 CVCMIServer::setState if value==2 命中 (mB_100124_r1_killer.txt)。

修复: setState 只改状态; 网络循环在 onPacketReceived 完成当前包后再停。
注: 若 SHUTDOWN 发生在无包处理期(训练场景不存在), 循环不退 —— 训练每局独立进程, 可接受。

幂等: 已打则 skip。写入前备份 <file>.bak_mlshutdown。
"""
import os
import shutil
import sys

ROOT = "/home/administrator/vcmi-native"
TARGET = os.path.join(ROOT, "server/CVCMIServer.cpp")
BAK = TARGET + ".bak_mlshutdown"

T = "\t"

OLD_STOP = (
    T + "state = value;\n\n"
    + T + "if (state == EServerState::SHUTDOWN)\n"
    + T + T + "networkHandler->stop();\n"
)

NEW_STOP = (
    T + "state = value;\n\n"
    + T + "// ML fix (09-24): 不在此处立即 stop —— 胜负判定发生在包处理中途, 立即 stop 会截断\n"
    + T + "// 包流(PackageApplied/胜利包不再发) → 客户端 AI 永久等 realize → 冻结。\n"
    + T + "// 改为 onPacketReceived 完成当前包后停机 (见该函数尾部)。\n"
)

OLD_VISIT = (
    T + "CVCMIServerPackVisitor visitor(*this, this->gh, c);\n"
    + T + "pack->visit(visitor);\n"
    + "}"
)

NEW_VISIT = (
    T + "CVCMIServerPackVisitor visitor(*this, this->gh, c);\n"
    + T + "pack->visit(visitor);\n\n"
    + T + "// ML fix (09-24): 当前包处理完再停机 (SHUTDOWN 语义延迟, 见 setState 注释)\n"
    + T + "if (state == EServerState::SHUTDOWN)\n"
    + T + T + "networkHandler->stop();\n"
    + "}"
)


def main():
    if not os.path.isfile(TARGET):
        print("file missing:", TARGET, file=sys.stderr)
        return 2
    src = open(TARGET, encoding="utf-8").read()
    if "ML fix (09-24): 不在此处立即 stop" in src:
        print("already patched")
        return 0
    if OLD_STOP not in src:
        print("anchor1 (setState stop) not found", file=sys.stderr)
        return 1
    if OLD_VISIT not in src:
        print("anchor2 (onPacketReceived tail) not found", file=sys.stderr)
        return 1
    if not os.path.exists(BAK):
        shutil.copy2(TARGET, BAK)
        os.utime(TARGET, None)
    src = src.replace(OLD_STOP, NEW_STOP, 1).replace(OLD_VISIT, NEW_VISIT, 1)
    open(TARGET, "w", encoding="utf-8").write(src)
    out = open(TARGET, encoding="utf-8").read()
    ok1 = "不在此处立即 stop" in out
    ok2 = "当前包处理完再停机" in out
    print("patched, verify:", ok1 and ok2)
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())