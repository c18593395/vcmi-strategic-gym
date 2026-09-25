#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 恢复段 vs 灾难前 S2 窗: 局/结束原因/战斗事件 对比评估。"""
import os
import re, statistics

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
lines = open(LOG, errors="replace").readlines()

SEGS = [
    ("灾难前S2窗", 105629, 111327),
    ("恢复段MMAI修复后", 111328, len(lines) + 1),
]

for tag, a, b in SEGS:
    seg = "".join(lines[a - 1: b])
    eps = re.findall(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=(-?[\d.]+) err=(\w+)", seg)
    rs = [float(e[3]) for e in eps]
    steps = [int(e[1]) for e in eps]
    errs = [e[4] for e in eps if e[4] != "no"]
    n = len(eps)
    print(f"\n== {tag}: {n} 局 ==")
    if not rs:
        continue
    print(f"  r: mean={statistics.mean(rs):.1f} median={statistics.median(rs):.1f} "
          f"min={min(rs):.1f} max={max(rs):.1f}")
    print(f"  步数: mean={statistics.mean(steps):.0f} median={statistics.median(steps):.0f} "
          f"(250=满步) | err局={len(errs)}")
    # 结束原因
    deaths = len(re.findall(r"\[HERO_DEATH\]", seg))
    zomb = len(re.findall(r"\[ZOMBIE\]", seg))
    cap = len(re.findall(r"\[TOWN_CAPTURE\]", seg))
    print(f"  结束相关行: HERO_DEATH x{deaths} ({deaths/max(1,n)*100:.0f}%) "
          f"ZOMBIE x{zomb} TOWN_CAPTURE x{cap}")
    # 战斗事件
    for pat in ["BHERO_CONTACT", "BHERO_ATTACK", "BHERO_SLAIN", "startBattle", "winner=0"]:
        c = len(re.findall(pat, seg))
        print(f"    {pat}: {c} ({c/max(1,n):.2f}/局)")
    # 大负局 (duel 底噪) 与高分局
    print(f"  r>=100 局: {sum(1 for r in rs if r >= 100)}  r<0 局: {sum(1 for r in rs if r < 0)}")
