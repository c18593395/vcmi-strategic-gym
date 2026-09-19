#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按行号分段统计 HERO_DEATH, 精确归属灾难前 vs 恢复段。"""
import re

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
lines = open(LOG, errors="replace").readlines()

SEGS = [
    ("灾难前S2窗", 105629, 111327),
    ("恢复段", 111328, len(lines) + 1),
]
for tag, a, b in SEGS:
    deaths = [i for i in range(a, min(b, len(lines) + 1)) if "HERO_DEATH" in lines[i - 1]]
    print(f"{tag} (行{a}..{b}): HERO_DEATH={len(deaths)}  "
          f"行号={[d for d in deaths][:30]}")
