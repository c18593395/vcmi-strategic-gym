#!/usr/bin/env python3
"""dump traj_ep.json 动作序列 — 实锤 econ_force 是否生效 (f7 溯源 2026-09-02)"""
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/traj_ep.json"
t = json.load(open(path))
acts = t.get("act", [])
print(f"total_steps={len(acts)}")
print("act[:40] =", acts[:40])
# 前 60 步分段摘要: 0-7 start_home 区 / 8-23 econ_force 区 / 24-59 move_to_force 区
print("act[0:8]   =", acts[0:8])
print("act[8:24]  =", acts[8:24])
print("act[24:60] =", acts[24:60])
eco = [i for i, a in enumerate(acts) if a in (16, 17, 18, 19, 20, 21)]
print(f"count 16-21 = {len(eco)}, first idx = {eco[:10]}")
