# -*- coding: utf-8 -*-
"""轮询 /tmp/traj_ep.json 直到完整(可解析), 输出该训练局的每步奖励与英雄位置"""
import json, time, sys

deadline = time.time() + 600
d = None
while time.time() < deadline:
    try:
        with open("/tmp/traj_ep.json", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("steps", 0) >= 190 and not d.get("error"):
            break
        d = None  # 太短(刚开头) 继续等
    except Exception:
        d = None
    time.sleep(10)

if d is None:
    print("10 分钟内未等到完整轨迹"); sys.exit(1)

obs0 = d["obs"][0]
nz = sum(1 for x in obs0 if x != 0)
MAP = {363: "20X20_01", 375: "20X20_02", 397: "30X30_01"}.get(nz, f"nz={nz}?")
print(f"steps={d.get('steps')} total_r={d.get('total_rew'):.2f} done={d.get('done')} → {MAP}")

GUARDS = {"20X20_01": [(5,6),(6,5)], "20X20_02": [(8,7),(9,6)], "30X30_01": [(7,7),(8,9),(9,8)]}.get(MAP)
acts, rews, nobss = d["act"], d["rew"], d["nobs"]
pos = []
for nobs in nobss:
    ah = int(nobs[3203]) if nobs[3203] >= 0 else 0
    b = 128 + ah * 26
    pos.append((int(nobs[b+2]), int(nobs[b+3])))

print("前 20 步:")
for i in range(min(20, len(pos))):
    hx, hy = pos[i]
    gd = min(abs(hx-gx)+abs(hy-gy) for gx, gy in GUARDS) if GUARDS else -1
    print(f"  {i:3d} a={acts[i]:2d} pos=({hx:2d},{hy:2d}) gd={gd:2d} r={rews[i]:+.2f}")
print("...")
big = [(i, round(v,2)) for i, v in enumerate(rews) if abs(v) > 2.0]
print(f"|r|>2 的步: {len(big)} 个: {big[:20]}")
cum = 0; cums = []
for v in rews:
    cum += v; cums.append(cum)
print(f"累计奖励: max={max(cums):.2f} (step {cums.index(max(cums))}), 终值={cums[-1]:.2f}")
