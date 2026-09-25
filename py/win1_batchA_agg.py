#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WIN-1 批次A 窗聚合 (A1): 按 WIN1_BATCH 行定位生效窗起点, 统计 ~40 局 + KL + min_d p50。
只读, 不碰训练。用法: wsl bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/win1_batchA_agg.py [窗口起始行号]"
窗口语义 (09-17 修正): L101674 首次开窗段 (step736372→739253, 22局) ep_runner 仍是旧代码
(零 BHERO_GRAD 输出 = P-H1 未生效), 视为污染段不计; 生效窗 = L102375 resume 起新代码。
默认取最后一个 WIN1_BATCH 行为窗起点 (resume 不断窗); 传行号可手动指定历史窗。
"""
import os
import re
import statistics
import sys

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
with open(LOG, errors="replace") as f:
    lines = f.readlines()

loads = [i for i, l in enumerate(lines, 1) if "Loaded train state" in l]
print("Loaded train state 行号(全部):", loads[-6:])

# 批次A 生效窗起点 = 最后一个 WIN1_BATCH 行 (L102375 resume 起新代码, 语义见文件头)
win1_lines = [i for i, l in enumerate(lines, 1) if "WIN1_BATCH" in l]
print(f"WIN1_BATCH 行号: {win1_lines}")
# 取最后一个 WIN1_BATCH 行作为生效窗起点 (窗内 resume 的 WIN1_BATCH 行即最新边界, 语义见文件头)
# 09-17: 此前误用 loads[-1] / enumerate 全文迭代 (EPS 误吃全历史 5349 局) — 双缺陷修正
start = win1_lines[-1]
if len(sys.argv) > 1:
    start = int(sys.argv[1])
print(f"批次A 生效窗起点 L={start}")

EPS = re.compile(r"ep_steps=(\d+) r=(-?[\d.]+) act=\[[0-9, ]*\] obs_nz=(\d+) map=(\S+)")
BGRAD = re.compile(r"\[BHERO_GRAD\] map=(\S+) grad_total=\+([\d.]+) cap=([\d.]+) "
                   r"final_min_d=(\S+) slain=(\S+) contact=(\S+)")
KL = re.compile(r"step(\d+) avg_r=(-?[\d.]+) vloss=[\d.-]+ loss=[\d.-]+ kl=([\d.]+) klc=([\d.]+)")

eps, bgrad, klpts = [], [], []
for ln, l in enumerate(lines[start:], start + 1):  # lines[] 0-based: start 行 = lines[start-1], 从下一行起统计
    m = EPS.search(l)
    if m:
        eps.append({"steps": int(m.group(1)), "r": float(m.group(2)),
                    "nz": int(m.group(3)), "map": m.group(4), "ln": ln})
    m = BGRAD.search(l)
    if m:
        bgrad.append({"map": m.group(1), "grad": float(m.group(2)),
                      "cap": float(m.group(3)), "mind": m.group(4),
                      "slain": m.group(5), "contact": m.group(6), "ln": ln})
    m = KL.search(l)
    if m:
        klpts.append({"step": int(m.group(1)), "kl": float(m.group(3)),
                      "klc": float(m.group(4)), "ln": ln})

print(f"窗口内局数: {len(eps)}  有效(nz>0): {sum(1 for e in eps if e['nz']>0)}")
print(f"BHERO_GRAD 行数: {len(bgrad)}  KL更新点: {len(klpts)}")

# 非 duel 图的 min_d 统计
non_duel = [b for b in bgrad if not b["map"].endswith("_duel.vmap")]
ds = sorted([int(b["mind"]) for b in non_duel if b["mind"] != "None"])
print(f"非duel BHERO_GRAD 局数: {len(non_duel)}  min_d 非None: {len(ds)}")
if ds:
    p50 = statistics.median(ds)
    print(f"min_d 列表: {ds}")
    print(f"p50={p50}  判据线64  (基线128)  达标: {'✅' if p50<64 else '❌'}")

# 平均 r
valid = [e for e in eps if e["nz"] > 0]
if valid:
    avg_r = statistics.mean(e["r"] for e in valid)
    print(f"窗口 avg_r={avg_r:.2f}  (基线 2.34, 判据: 跌幅<20% 即 avg_r>-0.234×...)")

# KL 峰值
if klpts:
    kl_max = max(klpts, key=lambda x: x["kl"])
    print(f"KL 峰值: step={kl_max['step']} kl={kl_max['kl']} klc={kl_max['klc']}")
    kl_high = [k for k in klpts if k["kl"] > 1.0]
    print(f"KL>1.0 的更新点: {len(kl_high)}/{len(klpts)}")
    if kl_high:
        for k in kl_high:
            print(f"  step={k['step']} kl={k['kl']} klc={k['klc']}")

# 截断率
trunc = sum(1 for e in valid if e["steps"] >= 200)
print(f"截断率: {trunc}/{len(valid)} = {trunc*100//max(len(valid),1)}%")

# 本窗 slain/contact 非空统计
slain_n = sum(1 for b in bgrad if b["slain"] != "[]")
contact_n = sum(1 for b in bgrad if b["contact"] != "[]")
print(f"slain 非空: {slain_n} 局   contact 非空: {contact_n} 局")

# 按图分组 r
from collections import defaultdict
by_map = defaultdict(list)
for e in valid:
    by_map[e["map"].replace(".vmap", "")].append(e["r"])
print("\n分图 r 均值 (本窗):")
for mp, rs in sorted(by_map.items()):
    print(f"  {mp:40s} n={len(rs):3d} avg={statistics.mean(rs):8.2f}")
