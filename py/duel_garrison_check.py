#!/usr/bin/env python3
"""验证冒烟局: 兵是否进了 garrison 而非英雄部队 (RECRUITED=0 最终实锤)
读 traj JSON 的 obs, 解码 城驻军 field 6-12 + 英雄 army field 15-21 (hero 段布局见 ep_runner P2 注)
obs 布局: hero 段 base=3203? 不对 — heroes 段布局见 ep_runner L1727: int(nobs[3203]) = 红英雄 slot 索引相关
用法: wsl venv-python duel_garrison_check.py /tmp/duel_smoke_out_1.json
"""
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/duel_smoke_out_1.json"
t = json.load(open(path))
obs = t.get("obs") or t.get("obss") or []
if not obs:
    print("traj 无 obs, keys:", list(t.keys())[:20]); sys.exit(0)

print(f"steps={len(obs)} obs_dim={len(obs[0])}")
# 城槽 garrison: obs 城段 field 6-12 (fill_v3_fields 驻军 7 档 count)
# 城段基址: 项目 obs 布局 towns 段 — 从 ep_runner L454-462 资源段推断 towns 在 [..];
# 直接扫描: 打印 step0-20 的 城驻军候选窗口 (garrison 7 数) 与 hero army 7 数
# hero army: field 15-21 于 hero 槽 (L1722: army 7 个纯 count 在 field 15-21)
# hero 槽基址 = 3203 存的是 slot 索引? L811: _ah3 = int(obs[3203]) → 英雄索引; _hb3 = 128 + _ah3*26 → hero 段基址
print("\nstep | hero_army[7] (field+15..21) | 变化")
prev = None
for s in range(min(len(obs), 250)):
    o = obs[s]
    ah = int(o[3203])
    if ah < 0:
        if s < 5: print(f"{s:4d} | hero dead frame")
        continue
    hb = 128 + ah * 26
    army = [int(o[hb + 15 + i]) for i in range(7)]
    if army != prev:
        print(f"{s:4d} | {army}")
        prev = army
    if s > 60 and prev is not None:
        break
print("\n(若 step2-4 后 army 无变化而终局 garrison 增 → 兵落 garrison 实锤)")
# 城 garrison: towns 段 — 找 obs 中 7 连 count 值在 step2-4 后增长的非 hero 段
print("\n扫描 towns 段 garrison 增长窗口 (粗扫: 值在 step1→step6 期间增加的位置):")
if len(obs) > 6:
    d0, d6 = obs[1], obs[min(6, len(obs)-1)]
    inc = [(i, int(d6[i]) - int(d0[i])) for i in range(len(d0))
           if isinstance(d0[i], (int, float)) and d6[i] > d0[i] and d0[i] >= 0]
    for i, dv in inc[:25]:
        print(f"  obs[{i}]: {int(d0[i])} -> {int(d6[i])} (+{dv})")
