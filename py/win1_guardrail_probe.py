#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批次A 生效窗护栏判据计数 (WIN-1 ②④⑤不塌: 守卫胜闭环/自发经济/局长分布). 只读."""
import re
import statistics

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
with open(LOG, errors="replace") as f:
    lines = f.readlines()

start = max(i for i, l in enumerate(lines, 1) if "WIN1_BATCH" in l)  # L102375 生效窗
seg = lines[start:]
j = "".join(seg)

print(f"生效窗起点 L={start}, 段内行数={len(seg)}")
print(f"TOWN_CAPTURE 事件: {len(re.findall(r'TOWN_CAPTURE', j))}")
print(f"[GUARD]/BHERO_KILL 事件: {len(re.findall(r'\[GUARD\]|BHERO_KILL', j))}")
print(f"RECRUITED 事件: {len(re.findall(r'RECRUITED', j))}")
print(f"[ECON] 事件: {len(re.findall(r'\[ECON\]', j))}")
print(f"[START_HOME] 局: {len(re.findall(r'START_HOME\] begin', j))}")

eps = [int(m) for m in re.findall(r"ep_steps=(\d+)", j)]
if eps:
    print(f"局长分布: n={len(eps)} mean={statistics.mean(eps):.0f} median={statistics.median(eps)} "
          f"min={min(eps)} max={max(eps)} 截断(>=200)={sum(1 for e in eps if e >= 200)}/{len(eps)}")

rs = [float(m) for m in re.findall(r"ep_steps=\d+ r=(-?[\d.]+)", j)]
if rs:
    pos = sum(1 for r in rs if r > 0)
    print(f"r 分布: 正局 {pos}/{len(rs)} ({pos*100//len(rs)}%)  top3={sorted(rs)[-3:]}  bottom3={sorted(rs)[:3]}")

# TOWN_VISIT/取兵窗有效率: TOWN_VISIT 后 4 步内 RECRUITED (观察事件) — 粗口径: 比例
tv = len(re.findall(r"TOWN_VISIT", j))
print(f"TOWN_VISIT 窗: {tv}  (对照 RECRUITED 观察事件见上)")
