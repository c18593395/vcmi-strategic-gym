#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4: ZOMBIE/ENDTURN_FUSE 死锁事件聚合分析 (纯只读, 离线日志)

数据源: train_loop.log (全部历史 ep 行 + 转储的 [ZOMBIE]/[ENDTURN_FUSE] 标记)。
hermes_ep_*.log 逐局覆盖且 /tmp 重启即清, 只能当"当前局明细", 历史统计以主日志为准。

切分: 以 "Loaded train state (model+optimizer, step=N)" 横幅为纪元边界 (每次重启一段)。
口径: 首胜 = r>=80 且 steps<60; 僵尸局 = [ZOMBIE] 标记; 熔断局 = [ENDTURN_FUSE];
      空转局 = steps==1 且 r<5 (引擎崩溃段特征); 大负局 = r<-100。

用法: python3 py/analyze_deadlock.py [log路径]
"""
import re, sys

LOG = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
WIN_R, WIN_STEPS = 80.0, 60

m_ep = re.compile(r"ep_steps=(\d+)\s+r=([-\d.]+)")
m_map = re.compile(r"map=(\S+)")
m_resume = re.compile(r"Loaded train state \(model\+optimizer, step=(\d+)\)")
m_zombie = re.compile(r"\[ZOMBIE\].*?step (\d+)")
m_fuse = re.compile(r"\[ENDTURN_FUSE\].*?step (\d+)")

segs = []           # [{resume_step, eps: [(steps, r, map)], zombies: [step], fuses: [step]}]
cur = {"resume_step": 0, "eps": [], "zombies": [], "fuses": []}
with open(LOG, errors="replace") as f:
    for line in f:
        mm = m_resume.search(line)
        if mm:
            if cur["eps"] or cur["zombies"] or cur["fuses"]:
                segs.append(cur)
            cur = {"resume_step": int(mm.group(1)), "eps": [], "zombies": [], "fuses": []}
            continue
        me = m_ep.search(line)
        if me:
            mp = m_map.search(line)
            cur["eps"].append((int(me.group(1)), float(me.group(2)), mp.group(1) if mp else "?"))
            continue
        mz = m_zombie.search(line)
        if mz:
            cur["zombies"].append(int(mz.group(1)))
            continue
        mf = m_fuse.search(line)
        if mf:
            cur["fuses"].append(int(mf.group(1)))
if cur["eps"] or cur["zombies"] or cur["fuses"]:
    segs.append(cur)

def seg_stats(seg):
    eps = seg["eps"]
    n = len(eps)
    rs = [r for _, r, _ in eps]
    wins = sum(1 for s, r, _ in eps if r >= WIN_R and s < WIN_STEPS)
    ones = sum(1 for s, r, _ in eps if s == 1 and r < 5)
    bign = sum(1 for r in rs if r < -100)
    avg = sum(rs) / n if n else 0.0
    return n, wins, ones, len(seg["zombies"]), len(seg["fuses"]), bign, avg

print(f"P4 死锁事件聚合 — {LOG}\n" + "=" * 88)
print(f"{'纪元(续训起点)':>16} | {'局数':>5} {'首胜':>4} {'空转':>4} {'ZOMBIE':>6} {'熔断':>4} {'大负':>4} {'avg_r':>7}")
total = dict(n=0, w=0, o=0, z=0, f=0, b=0)
for seg in segs:
    n, wins, ones, zn, fn, bn, avg = seg_stats(seg)
    if n == 0 and zn + fn == 0:
        continue
    total["n"] += n; total["w"] += wins; total["o"] += ones
    total["z"] += zn; total["f"] += fn; total["b"] += bn
    print(f"step={seg['resume_step']:<10} | {n:>5} {wins:>4} {ones:>4} {zn:>6} {fn:>4} {bn:>4} {avg:>7.1f}")
print("-" * 88)
tn = total["n"] or 1
print(f"{'合计':>16} | {total['n']:>5} {total['w']:>4} {total['o']:>4} {total['z']:>6} {total['f']:>4} {total['b']:>4}"
      f"   zombie率={total['z']/tn:.1%} 空转率={total['o']/tn:.1%} 首胜率={total['w']/tn:.1%}")

# ZOMBIE 死亡步位分布 (整体)
zsteps = [s for seg in segs for s in seg["zombies"]]
if zsteps:
    print(f"\nZOMBIE 死亡步位分布 (n={len(zsteps)}):")
    buckets = [(0, 30), (30, 50), (50, 80), (80, 120), (120, 201)]
    for lo, hi in buckets:
        c = sum(1 for s in zsteps if lo <= s < hi)
        print(f"  [{lo:>3},{hi:>3}): {'#'*min(c, 60)} {c}")

# 最近健康纪元 (最后一段) 的分图 zombie/短局统计
last = segs[-1] if segs else None
if last and last["eps"]:
    from collections import defaultdict
    by_map = defaultdict(list)
    for s, r, mp in last["eps"]:
        by_map[mp].append((s, r))
    print(f"\n最后纪元 (续训自 step={last['resume_step']}) 分图统计:")
    for mp, eps in sorted(by_map.items()):
        n = len(eps)
        rs = [r for _, r in eps]
        wins = sum(1 for s, r in eps if r >= WIN_R and s < WIN_STEPS)
        short = sum(1 for s, r in eps if s < 50 and not (s == 1 and r < 5))
        print(f"  {mp}: n={n} 首胜={wins} 短局(<50步非空转)={short} avg_r={sum(rs)/n:.1f} "
              f"max_r={max(rs):.1f} min_r={min(rs):.1f}")
