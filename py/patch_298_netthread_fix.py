#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#298 方案1 修复: 网络线程内禁止等待 realize (框架级兜底, 09-23)

根因: 红方 MMAI 的 yourTurn 经 visitPlayerStartsTurn 在 runNetwork 线程同步执行,
      其 endTurn -> CClient::sendRequest(waitTillRealize=true) 阻塞网络线程;
      而解除阻塞的 visitPackageApplied(NetPacksClient.cpp:927) 只能由同一线程处理
      -> 自锁 -> 服务器空转 -> 300s adventure_wait 超时 -> 静默吞局。

修复: 给 CClient 加 static thread_local 网络线程标记, threadRunNetwork 入口置位;
      sendRequest 在该线程内跳过 waitWhileContains (只跳过等待, 请求照发, 逻辑零变更)。

运行: wsl -u root bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/patch_298_netthread_fix.py"
回退: 同命令加 rollback
"""
import os
import shutil
import sys

BASE = os.environ.get("BASE", "/home/administrator/vcmi-native")
CH = BASE + "/client/Client.h"
CC = BASE + "/client/Client.cpp"
CSH = BASE + "/client/CServerHandler.cpp"

T = "\t"

H_DECL = (
    T + "// ML fix (09-23, #298): 网络线程标记 — 该线程内禁止等待 realize\n"
    + T + "// (PackageApplied 只能由网络线程处理, 在其上等待即自锁)\n"
    + T + "static thread_local bool onNetworkThread;\n"
)

CPP_DEF = (
    "// ML fix (09-23, #298): 网络线程标记定义 (由 CServerHandler::threadRunNetwork 置位)\n"
    "thread_local bool CClient::onNetworkThread = false;\n\n"
)

OLD_WAIT = (
    T + "if(waitTillRealize)\n"
    + T + "{\n"
    + T * 2 + 'logGlobal->trace("We\'ll wait till request %d is answered.\\n", requestID);\n'
    + T * 2 + "auto gsUnlocker = vstd::makeUnlockSharedGuard(CGameState::mutex);\n"
    + T * 2 + "waitingRequest.waitWhileContains(requestID);\n"
    + T + "}\n"
)

NEW_WAIT = (
    T + "if(waitTillRealize)\n"
    + T + "{\n"
    + T * 2 + "if(CClient::onNetworkThread)\n"
    + T * 2 + "{\n"
    + T * 3 + "// ML fix (09-23, #298): 网络线程内跳过等待 — PackageApplied(解除等待的唯一路径)\n"
    + T * 3 + "// 只能由本线程处理, 在此等待 = 自锁 (实锤: 红方 MMAI yourTurn 经 visitPlayerStartsTurn\n"
    + T * 3 + "// 在 runNetwork 线程同步执行 endTurn → 300s adventure_wait 超时 → 静默吞局)\n"
    + T * 3 + 'fprintf(stderr, "[ML-fix] skip waitTillRealize on network thread: req=%d %s\\n", requestID, typeid(request).name());\n'
    + T * 2 + "}\n"
    + T * 2 + "else\n"
    + T * 2 + "{\n"
    + T * 3 + 'logGlobal->trace("We\'ll wait till request %d is answered.\\n", requestID);\n'
    + T * 3 + "auto gsUnlocker = vstd::makeUnlockSharedGuard(CGameState::mutex);\n"
    + T * 3 + "waitingRequest.waitWhileContains(requestID);\n"
    + T * 2 + "}\n"
    + T + "}\n"
)

EDITS = [
    # Client.h: 声明
    (CH, T + "ThreadSafeVector<int> waitingRequest;\n",
     T + "ThreadSafeVector<int> waitingRequest;\n\n" + H_DECL, 1),
    # Client.cpp: 定义 (放在 sendRequest 前)
    (CC, "int CClient::sendRequest(const CPackForServer & request, PlayerColor player, bool waitTillRealize)\n{\n",
     CPP_DEF + "int CClient::sendRequest(const CPackForServer & request, PlayerColor player, bool waitTillRealize)\n{\n", 1),
    # Client.cpp: 等待块改造
    (CC, OLD_WAIT, NEW_WAIT, 1),
    # CServerHandler.cpp: 入口置位
    (CSH, T + 'setThreadName("runNetwork");\n',
     T + 'setThreadName("runNetwork");\n'
     + T + 'CClient::onNetworkThread = true; // ML fix (09-23, #298): 网络线程标记\n', 1),
]

FILES = [CH, CC, CSH]
MARK = "ML fix (09-23, #298)"


def main():
    if "rollback" in sys.argv:
        for f in FILES:
            bak = f + ".bak_netfix298"
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
        print("[SKIP] 补丁已存在, 幂等退出")
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
    print("[OK] 锚点全量校验通过 (%d 处)" % len(EDITS))

    for f in FILES:
        shutil.copy2(f, f + ".bak_netfix298")
    for f, anchor, new, _e in EDITS:
        contents[f] = contents[f].replace(anchor, new, 1)
    for f in FILES:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(contents[f])
    print("[OK] 方案1 修复写入 %d 处 (备份 .bak_netfix298)" % len(EDITS))


if __name__ == "__main__":
    main()
