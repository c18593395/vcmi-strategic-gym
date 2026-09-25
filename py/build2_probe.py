#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A6 遗留排查: BUILD_2 (act20) 触发统计 — 主日志 highlights 白名单不含 [ECON],
first BUILD_2 +15 只能从 ep_steps 行的 act 序列统计验证 (窗口起点 = 最后 WIN1_BATCH 行)。"""
import os
import re

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
lines = open(LOG, errors="replace").readlines()
import sys
scope = sys.argv[1] if len(sys.argv) > 1 else "all"
if scope == "all":
    seg = lines
    start = 1
else:
    start = max(i for i, l in enumerate(lines, 1) if "WIN1_BATCH" in l)
    seg = lines[start:]

ep_re = re.compile(r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]*)\]")
n_ep = 0
n_act20 = 0
n_ep_with20 = 0
first20_eps = []
for l in seg:
    m = ep_re.search(l)
    if m:
        n_ep += 1
        acts = [int(x) for x in m.group(3).split(",") if x.strip()]
        c20 = acts.count(20)
        n_act20 += c20
        if c20:
            n_ep_with20 += 1
            first20_eps.append((m.group(1), m.group(2), c20))

print(f"窗起点 L={start}, 完结局 {n_ep}")
print(f"act=20 (BUILD_2): 总次数 {n_act20}, 出现局 {n_ep_with20}/{n_ep}")
for s, r, c in first20_eps[:10]:
    print(f"  steps={s} r={r} act20x{c}")
print("\n[ECON] 行在主日志可见性: highlights 白名单不含 [ECON] → 不可见 (观测假象源头)")
print("结论: act20>0 即 first BUILD_2 +15 已发生 (L1516-1519 无前置条件)")
