#!/usr/bin/env python3
"""检查 nounder 冒烟 traj: obs/terrain_grid 结构与非零统计."""
import json
import sys

for p in sys.argv[1:]:
    print(f"=== {p} ===")
    t = json.load(open(p))
    print("steps:", t.get("steps"), "| total_rew:", t.get("total_rew"), "| done:", t.get("done"))
    tg = t.get("terrain_grid")
    if tg is None:
        print("顶层无 terrain_grid")
    else:
        try:
            import numpy as np
            a = np.array(tg)
            print(f"terrain_grid: shape={a.shape} nonzero={int((a != 0).sum())} "
                  f"min={a.min()} max={a.max()}")
        except Exception as e:
            print(f"terrain_grid 解析失败: {e}")
