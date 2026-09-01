#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 T04 远目标下 C++ next_dir (obs[3330:3338]) 是否有效 (2026-08-29)
runner 逻辑: 24 → 选最近 target → next_dir_idx 匹配 → nd=obs[3330+idx]; nd>=0 用 C++ 全图路径, 否则回退 Python BFS(±7)/贪心"""
import json

TRAJ = "/tmp/traj_ep.json"
with open(TRAJ, encoding="utf-8") as f:
    d = json.load(f)

stats = {"nd_valid": 0, "nd_invalid": 0, "nd": {}}
for si in range(d["steps"]):
    obs = d["obs"][si]
    nds = [int(v) for v in obs[3330:3338]]
    for v in nds:
        stats["nd"][v] = stats["nd"].get(v, 0) + 1
    if any(v >= 0 for v in nds):
        stats["nd_valid"] += 1
    else:
        stats["nd_invalid"] += 1

print(f"steps={d['steps']}")
print(f"C++ next_dir 至少一个有效(>=0)的步数: {stats['nd_valid']}")
print(f"next_dir 全无效(=-1)的步数: {stats['nd_invalid']}")
print(f"next_dir 值分布: {dict(sorted(stats['nd'].items()))}")

# 抽样看 step 50 的 next_dir 与当前 target dist
obs = d["obs"][50] if d["steps"] > 50 else d["obs"][-1]
print(f"\nstep50 next_dir raw = {[int(v) for v in obs[3330:3338]]}")
tl = obs[3251:3315]
for i in range(8):
    row = [int(v) for v in tl[i*8:(i+1)*8]]
    if row[5] > 0:
        print(f"  target slot{i}: type={row[0]} pos=({row[2]},{row[3]}) dist={row[5]} -> next_dir={int(obs[3330+i])}")
