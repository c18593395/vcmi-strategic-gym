#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从最新 traj_ep.json 读取 obs[3251:3315] target_list, 检查 C++ 是否填入矿/城镇目标 (2026-08-29)
表结构: 8x8, 每目标 8 字段 = [type, idx, x, y, z, dist, power, flags] (ep_runner_one.py L361 注释)
对照 T04 vmap objects.json 的 mine/town/resource 坐标, 判断 target 覆盖情况"""
import json, zipfile, sys

TRAJ = "/tmp/traj_ep.json"
MAP = "T04_adventure_30X30_01.vmap"

with open(TRAJ, encoding="utf-8") as f:
    d = json.load(f)
if d.get("error"):
    print("traj error:", d["error"]); sys.exit(1)
print(f"steps={d['steps']} total_rew={d.get('total_rew'):.2f}")

# 取中期某步 (step 50) 的 obs, 避开 move_to_force 强制期
for si in [10, 50, 100, min(150, d["steps"]-1)]:
    if si >= d["steps"]:
        continue
    obs = d["obs"][si]
    tl = obs[3251:3315]
    print(f"\n== step {si} target_list:")
    n_used = 0
    for i in range(8):
        row = tl[i*8:(i+1)*8]
        t, idx, x, y, z, dist, power, flags = [int(v) for v in row]
        if dist > 0 or x != 0 or y != 0:
            n_used += 1
            print(f"  slot{i}: type={t} idx={idx} pos=({x},{y},{z}) dist={dist} power={power} flags={flags}")
    if n_used == 0:
        print("  (全空 — C++ 未填任何目标)")

# 对照 vmap 对象坐标
with zipfile.ZipFile(f"/mnt/d/Bigdata/hero3_fresh/maps/training/{MAP}") as z:
    o = json.loads(z.read("objects.json"))
print(f"\n== {MAP} 对象坐标:")
for k in sorted(o):
    if k.startswith(("mine", "town", "resource")):
        print(f"  {k}: ({o[k]['x']},{o[k]['y']})")

# 英雄实际位置 (obs 绝对坐标段)
obs = d["obs"][50] if d["steps"] > 50 else d["obs"][-1]
ah = int(obs[3203]) if obs[3203] >= 0 else 0
b = 128 + ah * 26
print(f"\nhero pos (obs): ({int(obs[b+2])},{int(obs[b+3])},{int(obs[b+4])})")
