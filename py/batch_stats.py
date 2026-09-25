#!/usr/bin/env python3
"""批转进度统计: report 汇总 + 当轮日志进度 (09-21)
用法: python py/batch_stats.py"""
import json
import os
import re
import time

ROOT = os.environ.get("ROOT", "/mnt/d/Bigdata/hero3_fresh")
REPORT = f"{ROOT}/maps/h3m_to_vmap/_pipeline_report.json"
LOG = f"{ROOT}/tmp/h3m_batch_run.log"
POOL = f"{ROOT}/maps/training/h3m_pool"

r = json.load(open(REPORT))
n = len(r)
stat = {}
for v in r.values():
    s = v.get("status", "?")
    stat[s] = stat.get(s, 0) + 1
pool_n = len([f for f in os.listdir(POOL) if f.endswith(".vmap")]) if os.path.isdir(POOL) else 0

print(f"== report 汇总 ({n} 条, 池文件 {pool_n}) ==")
for k in sorted(stat, key=stat.get, reverse=True):
    print(f"  {k:14s} {stat[k]:3d}  ({stat[k]*100//max(n,1)}%)")

# 当轮进度: 日志里最后出现的 [N/160]
cur_line = ""
started = ""
for line in open(LOG, errors="replace"):
    m = re.match(r"^\[(\d+)/(\d+)\]", line)
    if m:
        cur_line = line.rstrip()
        if m.group(1) == "1":
            started = cur_line
print(f"\n== 当轮起点: {started}")
print(f"== 最新进度: {cur_line}")

# 日志 mtime (活性)
age = time.time() - os.path.getmtime(LOG)
print(f"== 日志更新: {age:.0f}s 前 {'(活)' if age < 300 else '(⚠ 5 分钟无更新)'}")

# 最近 5 张结果
results = []
for line in open(LOG, errors="replace"):
    if "[PASS]" in line or "[FAIL]" in line or "[EVIDENCE]" in line:
        results.append(line.rstrip()[:110])
print("\n== 最近结果 ==")
for l in results[-5:]:
    print(" ", l)
