#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A3 own_town 衰减/拉黑 离线自测 (部署前): type_value 衰减数学 + score_candidates 整链。只读不改。"""
import sys
import numpy as np

sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")
import target_scorer as ts

# 1) type_value 衰减数学: 35×0.5^min(visits,3)
for v, exp in [(0, 35.0), (1, 17.5), (2, 8.75), (3, 4.375), (7, 4.375)]:
    c = {"is_own_town": True, "own_visits": v, "own_town_decay": 0.5}
    got = ts.type_value("economy", "own_town", False, c)
    assert abs(got - exp) < 1e-9, f"visits={v}: got {got} exp {exp}"
# 默认/decay=0 零行为
assert ts.type_value("economy", "own_town", False, {"is_own_town": True}) == 35.0
assert ts.type_value("economy", "own_town", False, {"is_own_town": True, "own_visits": 3, "own_town_decay": 0.0}) == 35.0
print("1) type_value 衰减数学 PASS")

# 2) score_candidates 整链 (最小 obs)
obs = [0.0] * 3464
obs[3203] = 0                                   # active hero = slot0
obs[128 + 0] = 1; obs[128 + 1] = 0              # hero id=1 owner=0 (红)
obs[128 + 2] = 5; obs[128 + 3] = 5; obs[128 + 4] = 0
obs[128 + 10] = 500                             # total_power
obs[336 + 0] = 7; obs[336 + 1] = 0              # town id=7 owner=0 (己方城)
obs[336 + 2] = 6; obs[336 + 3] = 5              # pos (6,5) 与 hero 曼哈顿=1
obs[336 + 14] = 1                               # recruit_mask bit0
obs[128 + 26 + 0] = 2; obs[128 + 26 + 1] = 1    # 蓝英雄 id=2 owner=1
obs[128 + 26 + 2] = 30; obs[128 + 26 + 3] = 30; obs[128 + 26 + 4] = 0
obs = np.array(obs, dtype=np.float32)

w = dict(ts.DEFAULT_W)

def pick(**kw):
    return ts.score_candidates(obs, 5, 5, 0, 500, False, False, False, set(), set(), "economy", w,
                               own_town_visits=kw.get("visits"), own_town_decay=kw.get("decay", 0.0),
                               own_town_blocked=kw.get("blocked"), own_town_max_visits=kw.get("maxv", 0))

# 零行为: own_town V=35 → score=35+55-0.5=89.5
s0 = pick()
ot0 = [x for x in s0 if x[1]["is_own_town"]]
assert ot0 and abs(ot0[0][2]["V"] - 35.0) < 1e-6 and abs(ot0[0][0] - 89.5) < 1e-6, f"{ot0}"
print(f"2a) 零行为 PASS: own_town V=35 score={ot0[0][0]:.1f} (基线 89.5)")

# 衰减 visits=1: V=17.5
ot1 = [x for x in pick(visits={7: 1}, decay=0.5) if x[1]["is_own_town"]]
assert ot1 and abs(ot1[0][2]["V"] - 17.5) < 1e-6
print(f"2b) 衰减 visits=1 PASS: V={ot1[0][2]['V']:.2f} score={ot1[0][0]:.1f}")

# 拉黑: 候选剔除
ot2 = [x for x in pick(visits={7: 1}, decay=0.5, blocked={7}) if x[1]["is_own_town"]]
assert not ot2
print("2c) 空撞拉黑 PASS: own_town 整类剔除")

# 硬上限: visits=4 >= max 4 → 剔除
ot3 = [x for x in pick(visits={7: 4}, decay=0.5, maxv=4) if x[1]["is_own_town"]]
assert not ot3
print("2d) 访问硬上限 PASS: visits=4>=4 剔除")

print("\nA3 自测全部通过 ✅")
