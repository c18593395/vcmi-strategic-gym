#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 S2 新基线专项: 恢复段 40 局按 10 局分段 + 按图死亡率交叉。"""
import re, statistics

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
lines = open(LOG, errors="replace").readlines()

# 恢复段起点(行号, 1-based)
START = 111328
seg_lines = lines[START - 1:]
seg = "".join(seg_lines)

# 解析所有 EP_TIME(全局行号从 START 算)
eps = []
for i, ln in enumerate(seg_lines, start=START):
    m = re.search(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=\d+ r=(-?[\d.]+) err=(\w+)", ln)
    if m:
        eps.append({"line": i, "map": m.group(1), "steps": int(m.group(2)),
                    "r": float(m.group(3)), "err": m.group(4)})

n = len(eps)
print(f"恢复段共 {n} 局, 行号 {START}..{lines and len(lines)}")

# 1) 10 局分段趋势
print("\n== 10 局分段趋势 ==")
for b in range(0, n, 10):
    chunk = eps[b:b + 10]
    rs = [e["r"] for e in chunk]
    deaths = sum(1 for e in chunk if "hero dead" in "".join(
        seg_lines[e["line"] - 1:e["line"] + 15]))
    print(f"  局{b+1:02d}-{b+len(chunk):02d}: r均值={statistics.mean(rs):7.1f} "
          f"min={min(rs):6.1f} max={max(rs):6.1f} "
          f"死亡率≈{deaths/len(chunk)*100:.0f}%  步数均值={statistics.mean([e['steps'] for e in chunk]):.0f}")

# 2) 按图死亡率(用 HERO_DEATH/ZOMBIE 行就近归到上一个 EP_TIME)
print("\n== 按图 r / HERO_DEATH ==")
by_map = {}
death_map = None
cur_map = None
death_events = []  # (line_no, map)
# 先扫全恢复段, 记录每个 EP_TIME 与其后到下个 EP_TIME 之间的 HERO_DEATH
line_marks = []
for e in eps:
    line_marks.append((e["line"], e["map"], e["r"]))
# 用区间: 每局范围 = [本局 EP_TIME 行, 下一局 EP_TIME 行)
import collections
map_r = collections.defaultdict(list)
map_death = collections.defaultdict(int)
for idx, (ln, mp, r) in enumerate(line_marks):
    end = line_marks[idx + 1][0] if idx + 1 < len(line_marks) else len(seg_lines) + 1
    block = "".join(seg_lines[ln:end])
    map_r[mp].append(r)
    map_death[mp] += block.count("[HERO_DEATH]")
total_death = sum(map_death.values())
for mp in sorted(map_r):
    rs = map_r[mp]
    d = map_death.get(mp, 0)
    print(f"  {mp:32s} {len(rs):2d}局 r均值={statistics.mean(rs):7.1f} "
          f"HERO_DEATH={d} ({d/len(rs)*100:.0f}%)")
print(f"  HERO_DEATH 总 {total_death} / {n} 局 = {total_death/max(1,n)*100:.0f}%")

# 3) 步数骤降的 duel 图: 看是不是被蓝方逼到提前全灭/困死
print("\n== duel 图步数分布 ==")
for mp in map_r:
    if "duel" in mp:
        steps_sorted = sorted(e["steps"] for e in eps if e["map"] == mp)
        print(f"  {mp}: 局数={len(steps_sorted)} 步数序列={steps_sorted}")
