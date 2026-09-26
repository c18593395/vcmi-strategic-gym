#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1-2 #298 对照实验 — 手术式 revert/apply 三套 298 补丁 (09-26)

背景: .so 级 .bak (libmlclient.so.bak_*298) 是 09-23 快照, 直接 rollback 会
误伤 09-24 的 [ML-time]/[ML-fix] game_over 等独立提交。故在**源码树**里手术式
逆向: 直接 import 三个补丁脚本的 EDITS(与正向同一份 anchor/new 字符串常量),
对每个 (anchor,new) 做 replace(new→anchor), 保证逐字还原、不碰其他改动。

- revert: 删三套 298(stk/netthread/upg), 保留 [ML-time]/game_over/tradecap 等
- apply : 用原 EDITS 的 anchor→new 重放, 恢复三套 298(锚点=原始文本, revert 后必在)

运行:  python3 revert_298.py revert|apply [check]
  check = 只干跑, 报告每项锚点命中, 不写文件
"""
import importlib.util
import os
import sys

BASE = os.environ.get("BASE", "/home/administrator/vcmi-native")
PY = "/mnt/d/Bigdata/hero3_fresh/py"

PATCHES = [
    ("patch_298_stacktrace.py", "stk"),
    ("patch_298_netthread_fix.py", "net"),
    ("patch_298_upgrade_probe.py", "upg"),
]


def load_edits(fname):
    path = os.path.join(PY, fname)
    spec = importlib.util.spec_from_file_location("p_" + fname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # if __name__ guard => main() 不跑
    return mod


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    check = "check" in sys.argv[1:]

    # 加载三套 EDITS
    all_edits = []
    for fname, tag in PATCHES:
        mod = load_edits(fname)
        for (f, anchor, new, expect) in mod.EDITS:
            all_edits.append((tag, fname, f, anchor, new, expect))

    print("=== 共 %d 项 EDITS (3 套) ===" % len(all_edits))

    if mode in ("revert", "check") and mode != "apply":
        # 逆向: new -> anchor
        bad = 0
        for tag, fname, f, anchor, new, expect in all_edits:
            c = open(f, encoding="utf-8").read()
            if new not in c:
                print("[WARN-%s] new 锚点缺失: %s (树可能已变/已 revert)" % (tag, os.path.basename(f)))
                bad += 1
                continue
            if check:
                print("[CHECK] 可逆: %s %s" % (tag, os.path.basename(f)))
                continue
            open(f, "w", encoding="utf-8").write(c.replace(new, anchor, 1))
            print("[OK-revert] %s %s" % (tag, os.path.basename(f)))
        if check:
            print("=== check 完 (%d 项缺锚点) ===" % bad)
        else:
            print("=== revert 完 (%d 项缺锚点) ===" % bad)
        return

    if mode == "apply":
        # 重放: anchor -> new
        for tag, fname, f, anchor, new, expect in all_edits:
            c = open(f, encoding="utf-8").read()
            if new in c:
                print("[SKIP] 已在: %s %s" % (tag, os.path.basename(f)))
                continue
            if anchor not in c:
                print("[FAIL] anchor 缺失: %s %s" % (tag, os.path.basename(f)))
                continue
            if check:
                print("[CHECK] 可 apply: %s %s" % (tag, os.path.basename(f)))
                continue
            open(f, "w", encoding="utf-8").write(c.replace(anchor, new, 1))
            print("[OK-apply] %s %s" % (tag, os.path.basename(f)))
        print("=== apply 完 ===")


if __name__ == "__main__":
    main()
