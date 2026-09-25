#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S2 撤梯子判据复查: avg_r 跌<20% + 招兵/建设频率不塌。
用法: s2_gate_check.py <窗起始行号> <窗名>  (可多次调用对比基线窗与 S2 窗)"""
import os
import re
import statistics
import sys

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
start = int(sys.argv[1])
tag = sys.argv[2] if len(sys.argv) > 2 else f"L{start}"

lines = open(LOG, errors="replace").readlines()
seg = lines[start - 1:]
j = "".join(seg)

# 局与 reward
eps = re.findall(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=(-?[\d.]+) err=(\w+)", j)
rs = [float(e[3]) for e in eps]
# 招兵/建设频率
n_recruited = len(re.findall(r"\[RECRUITED\]", j))
n_recruit_tier = len(re.findall(r"\[ECON\] recruit tier=", j))
n_build2 = len(re.findall(r"\[ECON\] build2 \(act20\)", j))
n_first_b2 = len(re.findall(r"first BUILD_2", j))
n_build_new = len(re.findall(r"\[BUILD_NEW\]", j))
n_lowdw = len(re.findall(r"low-tier dwelling built", j))
n_visit = len(re.findall(r"\[TOWN_VISIT\]", j))
n_s2val = len(re.findall(r"\+0\.25|\+0\.375", j))

print(f"== {tag} (L{start} 起, 段 {len(seg)} 行) ==")
if rs:
    print(f"局数={len(rs)} r: mean={statistics.mean(rs):.1f} median={statistics.median(rs):.1f} "
          f"min={min(rs):.1f} max={max(rs):.1f}")
print(f"招兵: [RECRUITED] x{n_recruited} ({n_recruited / max(1, len(rs)):.1f}/局), "
      f"[ECON] recruit tier x{n_recruit_tier} ({n_recruit_tier / max(1, len(rs)):.1f}/局)")
print(f"建设: build2 x{n_build2}, first BUILD_2 x{n_first_b2}, BUILD_NEW x{n_build_new}, "
      f"低档巢+3 x{n_lowdw}")
print(f"取兵窗: TOWN_VISIT x{n_visit} ({n_visit / max(1, len(rs)):.2f}/局)")
print(f"S2 新数值行 (+0.25/+0.375): {n_s2val}")
