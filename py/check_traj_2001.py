# -*- coding: utf-8 -*-
"""从 /tmp/traj_ep.json 提取最近一局的英雄真实轨迹 (ground truth)"""
import json

d = json.load(open("/tmp/traj_ep.json", encoding="utf-8"))
if d.get("error"):
    print("traj error:", d["error"])
obs0 = d["obs"][0]
nz = sum(1 for x in obs0 if x != 0)
MAP = {363: "20X20_01", 375: "20X20_02", 397: "30X30_01"}.get(nz, f"nz={nz}?")
print(f"steps={d.get('steps')} total_r={d.get('total_rew'):.2f} done={d.get('done')} map_nz={nz}→{MAP}")

GUARDS = {
    "20X20_01": [(5, 6), (6, 5)],
    "20X20_02": [(8, 7), (9, 6)],
    "30X30_01": [(7, 7), (8, 9), (9, 8)],
}[MAP] if MAP in ("20X20_01", "20X20_02", "30X30_01") else None

acts = d["act"]; rews = d["rew"]; nobss = d["nobs"]
pos_seq = []
for i, nobs in enumerate(nobss):
    ah = int(nobs[3203]) if nobs[3203] >= 0 else 0
    b = 128 + ah * 26
    hx, hy = int(nobs[b+2]), int(nobs[b+3])
    pos_seq.append((hx, hy))

print("前 50 步: step act  pos  min_guard_d  r")
for i in range(min(50, len(pos_seq))):
    hx, hy = pos_seq[i]
    mgd = min(abs(hx-gx)+abs(hy-gy) for gx, gy in GUARDS) if GUARDS else -1
    print(f"  {i:3d} a={acts[i]:2d} pos=({hx:2d},{hy:2d}) gd={mgd:2d} r={rews[i]:+.2f}")

# 全程: 是否踏守卫格 / 守卫距离变化
if GUARDS:
    visits = sum(1 for hx, hy in pos_seq if (hx, hy) in GUARDS)
    mind = min(min(abs(hx-gx)+abs(hy-gy) for gx, gy in GUARDS) for hx, hy in pos_seq)
    print(f"\n全程踏守卫格步数={visits}/{len(pos_seq)} 最近守卫距离={mind}")
# 非零奖励步
nzr = [(i, rews[i]) for i in range(len(rews)) if abs(rews[i]) > 0.2]
print(f"非零奖励步 (|r|>0.2): {len(nzr)} 个, 样本: {[(i, round(v,2)) for i, v in nzr[:15]]}")
