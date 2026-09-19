#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 探针: 解析 traj 中双英雄逐步轨迹, 验证 blue 英雄是否移动/战斗。"""
import json, sys

traj = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/traj_test.json"))
obs = traj["obs"]
acts = traj.get("act", [])
print(f"steps={len(obs)}  obs_len={len(obs[0])}  (OBS_DIM 契约=3464: {'OK' if len(obs[0]) == 3464 else 'MISMATCH!'})")

def heroes(o):
    out = []
    for slot in range(8):
        base = 128 + slot * 26
        bid = int(o[base])
        if bid > 0:
            out.append((slot, bid, int(o[base + 2]), int(o[base + 3])))
    return out

first = heroes(obs[0])
last = heroes(obs[-1])
print(f"开局英雄槽: {first}")
print(f"末步英雄槽: {last}")

# 按槽位输出轨迹摘要
for slot, bid, x, y in first:
    xs, ys, moves = [], [], 0
    prev = None
    for o in obs:
        h = [h for h in heroes(o) if h[0] == slot]
        if not h:
            continue
        _, _, x2, y2 = h[0]
        xs.append(x2); ys.append(y2)
        if prev and (x2, y2) != prev:
            moves += 1
        prev = (x2, y2)
    print(f"  slot{slot} bid={bid}: 移动 {moves}/{len(xs)} 步, "
          f"位置 {xs[0]},{ys[0]} -> {xs[-1]},{ys[-1]}, 活跃={'是' if moves > 2 else '否(站桩)'}")
