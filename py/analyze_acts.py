#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0910 日志深度分析: act 分布 / 固化度 / T06 长局行为画像 (capture 路径)
用法 (WSL): python3 py/analyze_acts.py [train_loop.log]
只统计最后一次 resume 之后。
"""
import re, sys, statistics
from collections import defaultdict, Counter

LOG = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
lines = open(LOG, errors="replace").read().splitlines()
start = 0
for i, l in enumerate(lines):
    if "Loaded train state" in l:
        start = i + 1
w = lines[start:]

pat_ep = re.compile(r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]+)\] obs_nz=(\d+) map=(\S+)")
eps = []
for l in w:
    m = pat_ep.search(l)
    if m:
        eps.append({"steps": int(m.group(1)), "r": float(m.group(2)),
                    "act": [int(x) for x in m.group(3).split(",")],
                    "nz": int(m.group(4)), "map": m.group(5)})

# act 语义表 (动作空间 24: 0-7 方向 / 10 END_TURN / 16-21 经济 / 20-21 ? / 24 MOVE_TO 中间语义)
NAMES = {0:"N",1:"NE",2:"E",3:"SE",4:"S",5:"SW",6:"W",7:"NW",10:"ENDTURN",
         16:"RECRUIT_T1",17:"RECRUIT_T2",18:"RECRUIT_T3",19:"BUILD",20:"BUILD2",21:"OTHER",24:"MOVE_TO"}

print(f"== 全局 act 分布 (n={len(eps)} 局, {sum(len(e['act']) for e in eps)} 步) ==")
allc = Counter(a for e in eps for a in e["act"])
total = sum(allc.values())
for a, c in allc.most_common(15):
    print(f"  a={a:2d} {NAMES.get(a,'?'):11s} {c:5d} ({c/total*100:.1f}%)")

print("\n== 固化度 (相邻重复率 = act[i]==act[i-1], 含跨局首步断开) ==")
for grp, sel in [("全部", None), ("T06(72X72)", lambda e: "72X72" in e["map"]), ("T05", lambda e: "T05" in e["map"])]:
    rep = tot = 0
    for e in eps:
        if sel and not sel(e): continue
        for i in range(1, len(e["act"])):
            tot += 1
            if e["act"][i] == e["act"][i-1]: rep += 1
    print(f"  {grp}: {rep}/{tot} = {rep/max(tot,1)*100:.1f}%")

print("\n== 同图 act 序列逐字复现检测 (固化剧本指纹) ==")
seq_map = defaultdict(list)
for e in eps:
    seq_map[e["map"]].append(tuple(e["act"]))
for mp, seqs in seq_map.items():
    c = Counter(seqs)
    dup = [(s, n) for s, n in c.items() if n > 1]
    print(f"  {mp.split('/')[-1][:30]}: {len(seqs)} 局, 逐字重复组合 {len(dup)} 种" +
          (f" 最高复现 {max(n for _,n in dup)} 次" if dup else ""))

print("\n== T06 长局解剖 (steps>=100, capture 路径画像) ==")
for e in eps:
    if e["steps"] >= 100:
        c = Counter(e["act"])
        dirs = sum(v for k, v in c.items() if k in (0,1,2,3,4,5,6,7))
        print(f"  {e['map'].split('/')[-1][:30]} steps={e['steps']} r={e['r']:.1f} "
              f"方向={dirs}({dirs/len(e['act'])*100:.0f}%) ENDTURN={c.get(10,0)} "
              f"经济16-21={sum(v for k,v in c.items() if 16<=k<=21)} "
              f"top3={[(NAMES.get(a,'?'),n) for a,n in c.most_common(3)]}")

print("\n== per-map r 时序 (前1/3 vs 后1/3, 上行=学习) ==")
for mp in sorted(set(e["map"] for e in eps)):
    rs = [e["r"] for e in eps if e["map"] == mp]
    if len(rs) >= 4:
        k = max(len(rs)//3, 1)
        print(f"  {mp.split('/')[-1][:30]}: n={len(rs)} 前1/3 avg={sum(rs[:k])/k:.1f} 后1/3 avg={sum(rs[-k:])/k:.1f}")
    else:
        print(f"  {mp.split('/')[-1][:30]}: n={len(rs)} (样本不足)")
