# -*- coding: utf-8 -*-
"""训练日志快速分析: 奖励分布 / 胜率代理 / 1步局定位 / 分图统计"""
import os
import re, sys, io

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
WINS = {"win"}  # 首胜判定: r>=80 且 steps<60 (与 eval_promo 同口径)

rs = []          # (line_no, steps, r, map)
cur_line = 0
pat = re.compile(r"ep_steps=(\d+) r=(-?[\d.]+)")
pat_map = re.compile(r"map=(\S+)")
with io.open(LOG, encoding="utf-8", errors="ignore") as f:
    for line in f:
        cur_line += 1
        m = pat.search(line)
        if m:
            mm = pat_map.search(line)
            rs.append((cur_line, int(m.group(1)), float(m.group(2)), mm.group(1) if mm else "?"))

print(f"total episodes: {len(rs)}  (lines={cur_line}, no_map={sum(1 for x in rs if x[3]=='?')})")

# 1步局分布
ones = [x for x in rs if x[1] == 1]
print(f"ep_steps=1: {len(ones)} 条, 行号范围 {ones[0][0]}-{ones[-1][0]}" if ones else "ep_steps=1: 0")
if ones and ones[-1][0] < len(rs) * 0.8:
    print("  -> 1步局全部在日志前部 (历史段), 非近期问题")

# 近期窗口统计
N = min(300, len(rs))
recent = rs[-N:]
rec_r = sorted(x[2] for x in recent)
mean_r = sum(rec_r) / N
p = lambda q: rec_r[int(N * q)]
win = sum(1 for _, s, r, _ in recent if r >= 80 and s < 60)
bigneg = sum(1 for r_ in rec_r if r_ <= -30)
print(f"\n--- 最近 {N} 局 ---")
print(f"mean_r={mean_r:.2f} min={rec_r[0]:.2f} p25={p(0.25):.2f} p50={p(0.5):.2f} p75={p(0.75):.2f} p90={p(0.9):.2f} max={rec_r[-1]:.2f}")
print(f"首胜代理 (r>=80 & steps<60): {win}/{N} = {100*win/N:.1f}%")
print(f"big_neg (r<=-30): {bigneg}/{N} = {100*bigneg/N:.1f}%")

# 分图统计 (最近 N 局)
from collections import defaultdict
by_map = defaultdict(list)
for _, s, r, m in recent:
    key = "30X30" if "30X30" in m else ("20X20_01" if "_01" in m else "20X20_02")
    by_map[key].append((s, r))
print("\n--- 分图 (最近 %d 局) ---" % N)
for k, v in sorted(by_map.items()):
    rr = [r for _, r in v]
    w = sum(1 for _, r in v if r >= 80)
    print(f"{k}: n={len(v)} mean_r={sum(rr)/len(rr):.2f} win={w} ({100*w/len(v):.1f}%)")

# 步数分布
step_hist = defaultdict(int)
for _, s, _, _ in rs:
    if s == 200: step_hist["200(满步)"] += 1
    elif s == 1: step_hist["1"] += 1
    elif s < 60: step_hist["<60(疑似首胜/zombie)"] += 1
    else: step_hist["60-199"] += 1
print("\n--- 全程步数分布 ---")
for k, v in sorted(step_hist.items()):
    print(f"{k}: {v}")
