#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按图分组对比死亡率: 守卫激活假设检验 (duel 图无中立怪, T05 有守卫)。"""
import re, statistics

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
lines = open(LOG, errors="replace").readlines()

SEGS = [("灾难前", 105629, 111327), ("恢复后", 111328, len(lines) + 1)]

for tag, a, b in SEGS:
    seg = "".join(lines[a - 1: b])
    eps = re.findall(r"\[EP_TIME\] map=(\S+?)\.vmap steps=(\d+) secs=\d+ r=(-?[\d.]+) err=(\w+)", seg)
    print(f"\n== {tag} ==")
    by_map = {}
    for m, st, r, err in eps:
        st, r = int(st), float(r)
        d = by_map.setdefault(m, [])
        d.append((st, r))
    for m, v in sorted(by_map.items()):
        n = len(v)
        # 死亡局近似: 该局日志段内 HERO_DEATH 无法直接按局归组, 用步数/r 辅助
        st_mean = statistics.mean(x[0] for x in v)
        r_mean = statistics.mean(x[1] for x in v)
        print(f"  {m}: {n} 局, 步数均值 {st_mean:.0f}, r 均值 {r_mean:.1f}")
    deaths = len(re.findall(r"HERO_DEATH", seg))
    print(f"  HERO_DEATH 总数: {deaths}")
