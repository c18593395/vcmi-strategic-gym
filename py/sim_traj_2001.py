# -*- coding: utf-8 -*-
"""20X20_01 vs 02 轨迹仿真: 从 train_loop.log 的 act 序列回放英雄位置, 检查守卫格到达情况"""
import re, io
from collections import Counter

# 方向向量 (ep_runner_one.py L451): d0=N(0,-1) d1=NE d2=E d3=SE d4=S d5=SW d6=W d7=NW
DX = [0, 1, 1, 1, 0, -1, -1, -1]
DY = [-1, -1, 0, 1, 1, 1, 0, -1]
GUARDS = {
    "T03_adventure_20X20_01.vmap": [(5, 6), (6, 5)],
    "T03_adventure_20X20_02.vmap": [(8, 7), (9, 6)],
    "T03_adventure_30X30_01.vmap": [(7, 7), (8, 9), (9, 8)],
}
HERO0 = {
    "T03_adventure_20X20_01.vmap": (7, 6),
    "T03_adventure_20X20_02.vmap": (5, 4),
    "T03_adventure_30X30_01.vmap": (8, 7),
}
# 资源点 (用于判断徘徊目标)
RES = {
    "T03_adventure_20X20_01.vmap": [(10, 5)],
    "T03_adventure_20X20_02.vmap": [(5, 15)],
    "T03_adventure_30X30_01.vmap": [(10, 10), (20, 5)],
}

pat = re.compile(r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]+)\] obs_nz=(\d+) map=(\S+)")
eps = {k: [] for k in GUARDS}
with io.open("/mnt/d/Bigdata/hero3_fresh/train_loop.log", encoding="utf-8", errors="ignore") as f:
    for line in f:
        m = pat.search(line)
        if m and m.group(5) in GUARDS:
            acts = [int(x) for x in m.group(3).split(",")]
            eps[m.group(5)].append((int(m.group(1)), float(m.group(2)), acts, int(m.group(4))))

for name in ["T03_adventure_20X20_01.vmap", "T03_adventure_20X20_02.vmap"]:
    print("\n" + "=" * 25, name, "=" * 25)
    print(f"局数={len(eps[name])}")
    arrive_cnt = 0
    mind_all = []
    for ei, (steps, r, acts, nz) in enumerate(eps[name]):
        hx, hy = HERO0[name]
        min_d = 10**9; arrive = False; res_visit = 0
        for a in acts:
            if a < 8:
                hx += DX[a]; hy += DY[a]
                hx = max(0, min(19, hx)); hy = max(0, min(19, hy))
            d = min(abs(hx-gx)+abs(hy-gy) for gx, gy in GUARDS[name])
            min_d = min(min_d, d)
            if d == 0: arrive = True
            if any(hx == rx and hy == ry for rx, ry in RES[name]): res_visit = 1
        mind_all.append(min_d)
        arrive_cnt += arrive
        if ei < 6 or arrive:  # 打印前6局 + 所有到达局
            print(f"  ep{ei}: steps={steps} r={r:.2f} min_guard_d={min_d} 到达守卫={arrive} 踩资源={res_visit} "
                  f"open={' '.join(map(str,acts[:12]))}")
    print(f"到达守卫格局数: {arrive_cnt}/{len(eps[name])}")
    print(f"全程最近守卫距离: mean={sum(mind_all)/len(mind_all):.2f} min={min(mind_all)} max={max(mind_all)}")
    # 动作直方图 (前30步 vs 后170步)
    c_open = Counter(); c_late = Counter()
    for _, _, acts, _ in eps[name]:
        c_open.update(acts[:30]); c_late.update(acts[30:])
    top = lambda c: " ".join(f"{k}:{v}" for k, v in c.most_common(8))
    print(f"前30步动作分布: {top(c_open)}")
    print(f"后170步动作分布: {top(c_late)}")
