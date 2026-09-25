#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批次B+A3 修复后首窗验证: 最近 WIN1_BATCH 行之后的双轨信号。只读。"""
import os
import re

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
with open(LOG, errors="replace") as f:
    lines = f.readlines()

start = max(i for i, l in enumerate(lines, 1) if "WIN1_BATCH" in l)
seg = lines[start:]
j = "".join(seg)
print(f"当前窗起点 L={start}, 段内 {len(seg)} 行")
for tag in ["TOWN_VISIT", "TOWN_EMPTY", "RECRUITED", "BHERO_CONTACT", "BHERO_KILL", "type=own_town"]:
    print(f"{tag}: {len(re.findall(tag, j))}")
print("---关键行---")
keep = [l.rstrip() for l in seg
        if re.search(r"TOWN_VISIT|TOWN_EMPTY|BHERO_CONTACT|BHERO_KILL|BHERO_GRAD|EP_TIME|ep_steps=|\[SCORE\]", l)]
for l in keep[:32]:
    print(l)
