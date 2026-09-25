#!/usr/bin/env python3
"""高负局 act 序列分析: 从主日志 ep_steps 行提取, 对比高负局 vs 正局模式 (09-21)"""
import os
import re
from collections import Counter

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
eps = []
for line in open(LOG, errors="replace"):
    m = re.search(r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]*)\]", line)
    if m:
        steps, r, acts = int(m.group(1)), float(m.group(2)), m.group(3)
        a = [int(x) for x in acts.split(",") if x.strip()]
        eps.append((r, steps, a))

print(f"日志内 ep_steps 行: {len(eps)} 局")
eps = eps[-120:]  # 只看恢复后最近窗口 (08:10 重启轮 + 前一轮尾部)
eps_sorted = sorted(eps, key=lambda e: e[0])

def mode_of(acts):
    """检测主导模式: END_TURN 占比 / 最长重复子序列 / 招兵建筑类占比"""
    c = Counter(acts)
    et = c.get(10, 0)
    econ = sum(v for k, v in c.items() if k >= 16)
    mv = sum(v for k, v in c.items() if k <= 7)
    top = c.most_common(4)
    return et, mv, econ, top

print("\n== 窗口内 rew 分布 ==")
import statistics
rs = [e[0] for e in eps]
print(f"n={len(rs)} min={min(rs):.0f} p25={sorted(rs)[len(rs)//4]:.0f} median={statistics.median(rs):.0f} p75={sorted(rs)[3*len(rs)//4]:.0f} max={max(rs):.0f} mean={statistics.mean(rs):.1f}")
neg300 = [e for e in eps if e[0] < -300]
pos = [e for e in eps if e[0] > 0]
print(f"高负(<-300): {len(neg300)} 局 / 正局(>0): {len(pos)} 局 ({len(pos)*100//len(eps)}%)")

print("\n== 窗口内最负 8 局 ==")
for r, steps, a in eps_sorted[:8]:
    et, mv, econ, top = mode_of(a)
    print(f"r={r:8.1f} steps={steps:3d} END_TURN={et:3d} 移动={mv:3d} 经济动作={econ:3d} top={top}")

print("\n== 窗口内最正 5 局 ==")
for r, steps, a in eps_sorted[-5:]:
    et, mv, econ, top = mode_of(a)
    print(f"r={r:8.1f} steps={steps:3d} END_TURN={et:3d} 移动={mv:3d} 经济动作={econ:3d} top={top}")

# 最负局动作周期性
print("\n== 窗口内最负局周期检测 ==")
r, steps, a = eps_sorted[0]
best = None
for p in range(2, 13):
    chunks = [tuple(a[i:i+p]) for i in range(0, len(a)-p+1)]
    c = Counter(chunks)
    pat, n = c.most_common(1)[0]
    cover = n * p / max(len(a), 1)
    if best is None or cover > best[2]:
        best = (pat, n, cover)
print(f"r={r} 主周期 pattern={list(best[0])} 出现 {best[1]} 次 覆盖率 {best[2]*100:.0f}%")
