#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ML 补丁存在性自检 —— 编译/训练前跑一遍，防上游重同步静默冲掉本地 ML 修复。

为什么需要它
------------
本地 ML 修复是以「工作区改动」形式存在的（不在 git 提交里），一旦把上游新版
源码覆盖进来，这些修复会被**静默覆盖且无任何报警**。2026-09-23 实测两处
08-17 修复就是这样丢的：

  * `server/CGameHandler.cpp` levelUpHero 「AI 玩家升级自动选第一个技能」
  * `server/battles/BattleResultProcessor.cpp` removeQuery 强制移除

两处都在 HEAD 里、都在工作区里消失，且是 09-19 上游同步时丢的，事后才发现。

用法
----
    python py/ml_patch_check.py                 # 检查默认树 /home/administrator/vcmi-native
    python py/ml_patch_check.py --root <路径>   # 指定源码树
    python py/ml_patch_check.py --json          # 机器可读输出

退出码
------
    0 = 所有「应存在」标记都在
    1 = 有「应存在」标记丢失（= 补丁被冲掉，禁止编译/训练）
    2 = 参数/环境错误（如源码树不存在）

登记新补丁：往 PATCHES 里加一行即可（id, 相对路径, 标记, 期望, 说明）。
期望取值：
    "present"      该修复应当存在于源码中；缺失即报错（这是真正的回归）
    "lost_pending" 已知丢失、待恢复；缺失只告警不报错（恢复后改成 present）
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_ROOT = "/home/administrator/vcmi-native"

# (id, 相对路径, grep 标记, 期望, 说明)
PATCHES = [
    # ---------- #298 三套补丁（09-23）----------
    ("298-stk", "server/queries/QueriesProcessor.cpp", "[ML-stk]", "present",
     "#298 查询栈打点（PUSH/POP/POPIFTOP/REMOVE）"),
    ("298-upg-cb", "AI/Nullkiller2/AIGateway.cpp", "_mlUpgLoop", "present",
     "#298 upgrade 死循环熔断 cap 8"),
    ("298-upg-log", "AI/Nullkiller2/AIGateway.cpp", "[ML-upg]", "present",
     "#298 upgrade 循环打点 + BREAK 标记"),
    ("298-netfix", "client/Client.cpp", "[ML-fix]", "present",
     "#298 方案1：网络线程内跳过 waitWhileContains"),
    ("298-netflag", "client/Client.h", "onNetworkThread", "present",
     "#298 网络线程标志（CClient::onNetworkThread）"),

    # ---------- ML fork 集成 ----------
    ("ml-tbb", "AI/Nullkiller2/AIGateway.cpp", "max_allowed_parallelism", "present",
     "TBB 限 4 线程防 OOM（C8.5，WSL 6GB 限制）"),
    ("ml-race", "AI/Nullkiller2/AIGateway.cpp", "a1ea3f4d2d", "present",
     "上游并发 race 修复摘取（09-06，AIStatus 锁迁移）"),
    ("ml-strategic", "server/CGameHandler.cpp", "strategic_state.h", "present",
     "战略层状态桥接（strategic_state）"),

    # ---------- 已恢复（09-23，py/patch_298_restore_0817.py）----------
    ("08-17-lvup", "server/CGameHandler.cpp", "isHuman())", "present",
     "08-17 AI 升级自动选技能（防 NK2 升级查询持锁死锁 → 刷屏卡死）— 09-23 按新上游结构恢复"),
    ("08-17-rmq", "server/battles/BattleResultProcessor.cpp", "queries->removeQuery(battleQuery);", "present",
     "08-17 战斗查询 removeQuery 任意位置强制移除 — 09-23 恢复"),
    ("09-14-qp-guard", "server/queries/QueriesProcessor.cpp", "bool removalDone", "absent",
     "09-14 修正: removeQuery 必须每玩家各调一次 onRemoval（守卫存在 = PvP 计数欠减回归，见踩坑 #228）"),
]


def check(root: Path):
    """返回 (results, hard_failures)。results 每项是 dict。"""
    results = []
    hard_failures = 0
    for pid, rel, marker, expect, note in PATCHES:
        path = root / rel
        if not path.is_file():
            results.append(dict(id=pid, file=rel, marker=marker, expect=expect,
                                status="FILE_MISSING", note=note))
            if expect in ("present", "absent"):
                hard_failures += 1
            continue
        try:
            found = marker in path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            results.append(dict(id=pid, file=rel, marker=marker, expect=expect,
                                status="READ_ERROR: %s" % exc, note=note))
            if expect in ("present", "absent"):
                hard_failures += 1
            continue

        if expect == "present":
            status = "OK" if found else "MISSING"
            if not found:
                hard_failures += 1
        elif expect == "absent":
            # 反向判据: 标记出现 = 修复被回归 (如上游同步把删掉的守卫又带回来)
            status = "REGRESSED" if found else "OK"
            if found:
                hard_failures += 1
        else:  # lost_pending
            status = "RESTORED" if found else "PENDING"

        results.append(dict(id=pid, file=rel, marker=marker, expect=expect,
                            status=status, note=note))
    return results, hard_failures


def main():
    ap = argparse.ArgumentParser(description="ML 补丁存在性自检")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="源码树根（默认 %s）" % DEFAULT_ROOT)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print("[ml_patch_check] 源码树不存在: %s" % root, file=sys.stderr)
        return 2

    results, hard_failures = check(root)

    if args.json:
        print(json.dumps(dict(root=str(root), hard_failures=hard_failures,
                              results=results), ensure_ascii=False, indent=2))
        return 1 if hard_failures else 0

    print("[ml_patch_check] root=%s" % root)
    print("%-12s %-9s %-46s %s" % ("id", "status", "file", "marker"))
    print("-" * 100)
    for r in results:
        print("%-12s %-9s %-46s %s" % (r["id"], r["status"], r["file"], r["marker"]))

    missing = [r for r in results if r["status"] in ("MISSING", "FILE_MISSING", "REGRESSED")]
    pending = [r for r in results if r["status"] == "PENDING"]
    restored = [r for r in results if r["status"] == "RESTORED"]

    print("-" * 100)
    if restored:
        for r in restored:
            print("[已恢复] %s — %s（可把 PATCHES 里该条 expect 改成 present）" % (r["id"], r["note"]))
    if pending:
        for r in pending:
            print("[待恢复] %s — %s" % (r["id"], r["note"]))
    if missing:
        print()
        for r in missing:
            print("[!! 丢失 !!] %s — %s\n            文件=%s  标记=%r\n            %s"
                  % (r["id"], "标记在源码里找不到，补丁很可能被上游同步冲掉了",
                     r["file"], r["marker"], r["note"]))
        print("\n结论：有 %d 个「应存在」的 ML 补丁丢失 —— 禁止编译/训练，先恢复补丁。" % len(missing))
        return 1

    print("结论：所有「应存在」的 ML 补丁都在（%d 项通过，%d 项待恢复）。"
          % (len(results) - len(pending), len(pending)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
