#!/usr/bin/env python3
"""batch1 表现观测: 重启以来 batch1 五图 vs 课程图对照 (09-22)
用法: python3 py/batch1_watch.py"""
import re
import statistics

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
BATCH1 = {
    "good_to_go_h3m.vmap", "judgement_day_h3m.vmap", "elbow_room_h3m.vmap",
    "a_viking_we_shall_go_h3m.vmap", "a_viking_we_shall_go_allied_h3m.vmap",
}

lines = open(LOG, errors="replace").readlines()
# 起点 = 最后一个 banner (最近一次重启)
start = 0
for i, ln in enumerate(lines):
    if "WSL2 PPO v2" in ln:
        start = i + 1

eps = []
for ln in lines[start:]:
    m = re.search(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=\d+ r=(-?[\d.]+) err=(\w+)", ln)
    if m:
        eps.append({"map": m.group(1), "steps": int(m.group(2)), "r": float(m.group(3))})

b1 = [e for e in eps if e["map"] in BATCH1]
cur = [e for e in eps if e["map"] not in BATCH1]

print(f"重启以来总局数: {len(eps)} (batch1={len(b1)} 课程图={len(cur)})")


def stat(ch, name):
    if not ch:
        print(f"  {name}: 无局")
        return
    rs = [e["r"] for e in ch]
    print(f"  {name}: n={len(ch)} r均值={statistics.mean(rs):.1f} min={min(rs):.1f} max={max(rs):.1f}")
    for e in ch:
        print(f"    - {e['map']:44s} steps={e['steps']:3d} r={e['r']:8.1f}")


print("\n== batch1 五图 ==")
stat(b1, "batch1")
print("\n== 课程图对照 ==")
if cur:
    rs = [e["r"] for e in cur]
    print(f"  课程图: n={len(cur)} r均值={statistics.mean(rs):.1f} min={min(rs):.1f} max={max(rs):.1f}")

# 护栏打点
n_black = sum(1 for ln in lines[start:] if "[SCORE_BLACK]" in ln)
n_drop = sum(1 for ln in lines[start:] if "[GUIDE_OSC_DROP]" in ln)
print(f"\n护栏: SCORE_BLACK={n_black} GUIDE_OSC_DROP={n_drop}")
