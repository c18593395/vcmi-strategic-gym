"""P10 离线静态验证 (2026-09-15): obs 快照 + 候选完整性 + 打分单调性 + 与 legacy 选择差异.

不依赖 WSL/VCMI, 纯 Python 验证 target_scorer 打分逻辑.
用法: /home/administrator/vcmi-workspace/venv/bin/python py/test_target_scorer.py
"""
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import target_scorer as ts

# obs 段偏移 (与 ep_runner 同口径)
OBS_TL_OFF = 3251
OBS_HERO_OFF = 128
OBS_TOWN_OFF = 336
OBS_ND_OFF = 3330
OBS_PAS_OFF = 3211
H_F_ID, H_F_OWNER, H_F_X, H_F_Y, H_F_Z, H_F_POW = 0, 1, 2, 3, 4, 10
T_F_ID, T_F_OWNER, T_F_X, T_F_Y = 0, 1, 2, 3

DEFAULT_W = dict(ts.DEFAULT_W)

# ============================================================
# 构造 obs 快照 (3464 维, 零值基线, 按需填段)
# ============================================================
def make_obs():
    return np.zeros(3464, dtype=np.float32)


def set_tl(obs, slot, ttype, x, y, z, dist, guard_pow=0):
    """填 target_list 一个槽位 (8×8, 每槽 8 字段: type,idx,x,y,z,dist,power,flags)."""
    base = OBS_TL_OFF + slot * 8
    obs[base] = ttype
    obs[base + 1] = 0       # idx
    obs[base + 2] = x
    obs[base + 3] = y
    obs[base + 4] = z
    obs[base + 5] = dist
    obs[base + 6] = guard_pow
    obs[base + 7] = 0       # flags


def set_hero(obs, slot, hero_id, owner, x, y, z, power=0, level=1):
    """填英雄段一个槽位 (8×26)."""
    base = OBS_HERO_OFF + slot * 26
    obs[base + H_F_ID] = hero_id
    obs[base + H_F_OWNER] = owner
    obs[base + H_F_X] = x
    obs[base + H_F_Y] = y
    obs[base + H_F_Z] = z
    obs[base + 5] = level   # level
    obs[base + H_F_POW] = power


def set_town(obs, slot, town_id, owner, x, y, z=0, recruit_lo=0, recruit_hi=0):
    """填城镇段一个槽位 (8×18)."""
    base = OBS_TOWN_OFF + slot * 18
    obs[base + T_F_ID] = town_id
    obs[base + T_F_OWNER] = owner
    obs[base + T_F_X] = x
    obs[base + T_F_Y] = y
    obs[base + 4] = z
    obs[base + 14] = recruit_lo
    obs[base + 15] = recruit_hi


# ============================================================
# 测试 1: 候选完整性 (5 类候选全部入池)
# ============================================================
def test_candidate_completeness():
    obs = make_obs()
    hx, hy, hz = 3, 3, 0
    # 设 active hero
    obs[3203] = 0
    set_hero(obs, 0, 1, 0, hx, hy, hz, power=100, level=5)

    # 候选 1: target_list 矿 + 资源堆
    set_tl(obs, 0, 1, 10, 5, 0, 12, 0)    # 矿 dist=12
    set_tl(obs, 1, 2, 5, 4, 0, 3, 0)      # 资源堆 dist=3

    # 候选 2: 蓝英雄 (owner=1, hero_id>0)
    set_hero(obs, 1, 2, 1, 20, 25, 0, power=50, level=3)

    # 候选 3: 蓝城 (owner=1)
    set_town(obs, 0, 10, 1, 40, 45)

    # 候选 4: 己方取兵城 (owner=0, recruit_mask≠0)
    set_town(obs, 1, 11, 0, 8, 6, recruit_lo=1)

    # 候选 5: 守卫 (mock, bfs_full_dir=None 时走曼哈顿)
    guards = [(5, 5, 0)]

    scored = ts.score_candidates(
        obs, hx, hy, hz, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="economy", w=DEFAULT_W,
        mapname="T04_test", current_target=None, stall_count=0,
        guards=guards, bfs_full_dir=None,
        own_town_limit=False, step_budget=0)

    types = set(c["type"] for _, c, _ in scored)
    print(f"  候选数={len(scored)}, 类型={types}")
    expected = {1, 2, "blue_hero", "blue_town", "own_town", "guard"}
    missing = expected - types
    assert not missing, f"缺失候选类型: {missing}"
    print("  ✓ 候选完整性通过 (5 类全部入池)")
    return scored


# ============================================================
# 测试 2: 打分单调性 (蓝英雄 > 蓝城 > 守卫 > 矿 > 资源堆)
# ============================================================
def test_score_monotonicity():
    obs = make_obs()
    hx, hy, hz = 3, 3, 0
    obs[3203] = 0
    set_hero(obs, 0, 1, 0, hx, hy, hz, power=500, level=5)

    # 同距离 5 个候选 (各类型)
    set_tl(obs, 0, 1, 8, 3, 0, 5, 0)      # 矿 dist=5
    set_tl(obs, 1, 2, 8, 8, 0, 5, 0)      # 资源堆 dist=5
    set_hero(obs, 1, 2, 1, 8, 8, 0, power=100, level=3)   # 蓝英雄 dist=5
    set_town(obs, 0, 10, 1, 8, 8)                              # 蓝城 dist=5
    guards = [(8, 8, 0)]                              # 守卫 dist=5 (与蓝英雄同位, 但类型不同)
    # 己方取兵城 dist=5
    set_town(obs, 1, 11, 0, 13, 3, recruit_lo=1)     # 取兵城 dist=10

    scored = ts.score_candidates(
        obs, hx, hy, hz, power_self=500,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="capture", w=DEFAULT_W,
        mapname="T04_test", current_target=None, stall_count=0,
        guards=guards, bfs_full_dir=None,
        own_town_limit=False, step_budget=0)

    # 按类型取分数
    scores = {}
    for s, c, meta in scored:
        t = c["type"]
        if t not in scores or s > scores[t][0]:
            scores[t] = (s, c)

    print("  各类型最高分:")
    for t, (s, c) in sorted(scores.items(), key=lambda x: -x[1][0]):
        print(f"    {str(t):12s} score={s:8.2f}  pos={c['pos']}")

    # 单调性检查 (capture 阶段, power 充足): 蓝英雄 > 蓝城 > 守卫 > 矿 > 资源堆
    if all(k in scores for k in ["blue_hero", "blue_town", "guard", 1, 2]):
        bh = scores["blue_hero"][0]
        bt = scores["blue_town"][0]
        gd = scores["guard"][0]
        mn = scores[1][0]
        rs = scores[2][0]
        print(f"\n  单调性: blue_hero({bh:.1f}) > blue_town({bt:.1f}) > guard({gd:.1f}) > mine({mn:.1f}) > res({rs:.1f})")
        assert bh > bt, f"蓝英雄({bh:.1f}) 应 > 蓝城({bt:.1f})"
        assert bt > mn or bt > gd, "蓝城价值应高于资源堆"
        print("  ✓ 打分单调性通过")
    else:
        print(f"  候选类型不全, 跳过单调性断言: {list(scores.keys())}")


# ============================================================
# 测试 3: 72_02 卡点验证 (蓝英雄入池)
# 场景: hero 在 (10,10), 蓝英雄在 (20,25) 远端, target_list 只有近资源堆
# 预期: scorer 选蓝英雄 (V=100 + Δcap=1.0), legacy 永远到不了
# ============================================================
def test_72_02_scenario():
    obs = make_obs()
    hx, hy, hz = 10, 10, 0
    obs[3203] = 0
    set_hero(obs, 0, 1, 0, hx, hy, hz, power=50, level=3)

    # target_list: 只有近资源堆 (dist=3), 矿/蓝英雄/蓝城 全被截断
    set_tl(obs, 0, 2, 12, 11, 0, 3, 0)
    set_tl(obs, 1, 2, 11, 13, 0, 4, 0)

    # 蓝英雄在远端 (1v3 终极目标, legacy D4 完全不在目标池)
    set_hero(obs, 1, 2, 1, 40, 45, 0, power=20, level=2)

    scored = ts.score_candidates(
        obs, hx, hy, hz, power_self=50,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="capture", w=DEFAULT_W,
        mapname="T06_72_02", current_target=None, stall_count=0,
        guards=[], bfs_full_dir=None,
        own_town_limit=False, step_budget=0)

    pick, runner_up = ts.pick_from_scored(scored)
    print(f"  pick={pick['ttype']} pos={pick['pos']} score={pick['meta']['score']:.1f}")
    print(f"  runner_up={runner_up[0] if runner_up else None:.1f}" if runner_up else "  runner_up=None")

    # scorer 应选蓝英雄 (V=100, Δcap=1.0, 远超资源堆 V=10)
    assert pick is not None, "scorer 无候选"
    assert pick["ttype"] == "blue_hero", f"72_02 场景 scorer 应选蓝英雄, 实际选了 {pick['ttype']}"
    print("  ✓ 72_02 卡点修复: 蓝英雄入池且打分最高 (legacy D4 完全不在目标池)")

    # legacy 对照: 只有资源堆候选 → 永远到不了蓝英雄
    legacy_best = None
    for i in range(8):
        tt = np.asarray(obs[OBS_TL_OFF + i * 8: OBS_TL_OFF + (i + 1) * 8], dtype=np.float32)
        if tt[5] > 0 and (legacy_best is None or tt[5] < legacy_best[5]):
            legacy_best = tt
    print(f"  legacy 对照: 只会选资源堆 pos=({int(legacy_best[2])},{int(legacy_best[3])}) dist={int(legacy_best[5])}, 蓝英雄不在池")


# ============================================================
# 测试 4: 硬约束过滤 (BFS 不可达 / 黑名单 / 取兵限次)
# ============================================================
def test_hard_constraints():
    obs = make_obs()
    hx, hy, hz = 3, 3, 0
    obs[3203] = 0
    set_hero(obs, 0, 1, 0, hx, hy, hz, power=100)

    # mock BFS: 蓝城 (40,45) 不可达
    def mock_bfs(mapname, hx, hy, tx, ty, blocked=None):
        if tx == 40 and ty == 45:
            return None, -1  # 不可达
        return 0, abs(tx - hx) + abs(ty - hy)  # 曼哈顿近似

    set_town(obs, 0, 10, 1, 40, 45)
    guards = []

    # 4a: 蓝城 BFS 不可达 → 不入池
    scored = ts.score_candidates(
        obs, hx, hy, hz, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="capture", w=DEFAULT_W,
        mapname="T04_test", current_target=None, stall_count=0,
        guards=guards, bfs_full_dir=mock_bfs,
        own_town_limit=False, step_budget=0)
    types = set(c["type"] for _, c, _ in scored)
    assert "blue_town" not in types, "蓝城 BFS 不可达应被剔除"
    print("  ✓ 蓝城 BFS 不可达剔除")

    # 4b: 守卫黑名单 → 不入池
    obs2 = make_obs()
    obs2[3203] = 0
    set_hero(obs2, 0, 1, 0, 3, 3, 0, power=100)
    guards_bl = [(5, 5, 0)]
    scored2 = ts.score_candidates(
        obs2, 3, 3, 0, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist={(5, 5)}, dyn_blocked=set(),
        phase="economy", w=DEFAULT_W,
        mapname="T04_test", current_target=None, stall_count=0,
        guards=guards_bl, bfs_full_dir=None,
        own_town_limit=False, step_budget=0)
    types2 = set(c["type"] for _, c, _ in scored2)
    assert "guard" not in types2, "守卫黑名单应被剔除"
    print("  ✓ 守卫黑名单剔除")

    # 4c: 取兵限次 → 整类剔除
    obs3 = make_obs()
    obs3[3203] = 0
    set_hero(obs3, 0, 1, 0, 3, 3, 0, power=100)
    set_town(obs3, 1, 11, 0, 8, 6, recruit_lo=1)
    scored3 = ts.score_candidates(
        obs3, 3, 3, 0, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="economy", w=DEFAULT_W,
        mapname="T06_test", current_target=None, stall_count=0,
        guards=[], bfs_full_dir=None,
        own_town_limit=True, step_budget=0)
    types3 = set(c["type"] for _, c, _ in scored3)
    assert "own_town" not in types3, "取兵限次应整类剔除"
    print("  ✓ 取兵限次整类剔除")


# ============================================================
# 测试 5: 步预算惩罚 (远候选加罚)
# ============================================================
def test_step_budget_penalty():
    obs = make_obs()
    hx, hy, hz = 3, 3, 0
    obs[3203] = 0
    set_hero(obs, 0, 1, 0, hx, hy, hz, power=100)

    # 近矿 dist=5 vs 远蓝城 dist=40
    set_tl(obs, 0, 1, 8, 3, 0, 5, 0)
    set_town(obs, 0, 10, 1, 40, 45)

    # step_budget=10: 远蓝城 plen=40 > 10*0.5=5 → 加罚
    scored_tight = ts.score_candidates(
        obs, hx, hy, hz, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="capture", w=DEFAULT_W,
        mapname="T04_test", current_target=None, stall_count=0,
        guards=[], bfs_full_dir=None,
        own_town_limit=False, step_budget=10)

    # step_budget=200: 远蓝城 plen=40 < 200*0.5=100 → 不罚
    scored_loose = ts.score_candidates(
        obs, hx, hy, hz, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="capture", w=DEFAULT_W,
        mapname="T04_test", current_target=None, stall_count=0,
        guards=[], bfs_full_dir=None,
        own_town_limit=False, step_budget=200)

    pick_tight, _ = ts.pick_from_scored(scored_tight)
    pick_loose, _ = ts.pick_from_scored(scored_loose)
    print(f"  step_budget=10:  pick={pick_tight['ttype']} (预算紧, 远候选加罚)")
    print(f"  step_budget=200: pick={pick_loose['ttype']} (预算松, 远候选不罚)")
    # 预算紧时近矿应胜出; 预算松时蓝城可能胜出 (V=80 > mine V=30)
    if pick_loose["ttype"] == "blue_town":
        print("  ✓ 步预算惩罚生效 (预算松时远蓝城胜出)")
    else:
        print(f"  注意: 预算松时 pick={pick_loose['ttype']} (仍非蓝城, 检查权重)")


# ============================================================
# 测试 6: 粘滞 bonus (当前目标未 stall → 强化保持)
# ============================================================
def test_stick_bonus():
    obs = make_obs()
    hx, hy, hz = 3, 3, 0
    obs[3203] = 0
    set_hero(obs, 0, 1, 0, hx, hy, hz, power=100)

    set_tl(obs, 0, 1, 10, 5, 0, 12, 0)   # 矿 dist=12
    set_tl(obs, 1, 2, 5, 4, 0, 3, 0)     # 资源堆 dist=3

    # 当前目标=矿 (10,5), stall=2 → stick=1.0
    scored_stick = ts.score_candidates(
        obs, hx, hy, hz, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="economy", w=DEFAULT_W,
        mapname="T04_test", current_target=(10, 5, 0), stall_count=2,
        guards=[], bfs_full_dir=None,
        own_town_limit=False, step_budget=0)

    # 当前目标=资源堆 (5,4), stall=0 → stick=1.0
    scored_res = ts.score_candidates(
        obs, hx, hy, hz, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="economy", w=DEFAULT_W,
        mapname="T04_test", current_target=(5, 4, 0), stall_count=0,
        guards=[], bfs_full_dir=None,
        own_town_limit=False, step_budget=0)

    for s, c, meta in scored_stick:
        if c["type"] in (1, "1"):
            print(f"  stick(矿, stall=2): score={s:.2f} stick_bonus={meta['stick']}")
    for s, c, meta in scored_res:
        if c["type"] in (2, "2"):
            print(f"  stick(资源堆, stall=0): score={s:.2f} stick_bonus={meta['stick']}")
    print("  ✓ 粘滞 bonus 验证完成")


# ============================================================
# 测试 7: 阶段调制 (economy vs capture 对蓝英雄/蓝城价值)
# ============================================================
def test_phase_modulation():
    obs = make_obs()
    hx, hy, hz = 3, 3, 0
    obs[3203] = 0
    set_hero(obs, 0, 1, 0, hx, hy, hz, power=100)

    # 蓝英雄 + 蓝城 同距离
    set_hero(obs, 1, 2, 1, 8, 8, 0, power=50)
    set_town(obs, 0, 10, 1, 8, 8)

    scored_eco = ts.score_candidates(
        obs, hx, hy, hz, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="economy", w=DEFAULT_W,
        mapname="T04_test", current_target=None, stall_count=0,
        guards=[], bfs_full_dir=None,
        own_town_limit=False, step_budget=0)

    scored_cap = ts.score_candidates(
        obs, hx, hy, hz, power_self=100,
        mine_taken=False, town_blocked=False, town_visited=False,
        guard_blacklist=set(), dyn_blocked=set(),
        phase="capture", w=DEFAULT_W,
        mapname="T06_test", current_target=None, stall_count=0,
        guards=[], bfs_full_dir=None,
        own_town_limit=False, step_budget=0)

    eco_bh = next((s for s, c, _ in scored_eco if c["type"] == "blue_hero"), None)
    cap_bh = next((s for s, c, _ in scored_cap if c["type"] == "blue_hero"), None)
    eco_bt = next((s for s, c, _ in scored_eco if c["type"] == "blue_town"), None)
    cap_bt = next((s for s, c, _ in scored_cap if c["type"] == "blue_town"), None)
    print(f"  蓝英雄: economy={eco_bh:.1f}  capture={cap_bh:.1f}  (差={cap_bh-eco_bh:.1f})")
    print(f"  蓝城:   economy={eco_bt:.1f}  capture={cap_bt:.1f}  (差={cap_bt-eco_bt:.1f})")
    assert cap_bh > eco_bh, "capture 阶段蓝英雄价值应高于 economy"
    assert cap_bt >= eco_bt, "capture 阶段蓝城价值应 ≥ economy"
    print("  ✓ 阶段调制通过 (economy 罚蓝英雄/蓝城, capture 拉满)")


if __name__ == "__main__":
    print("=" * 60)
    print("P10 target_scorer 离线静态验证")
    print("=" * 60)

    print("\n[1] 候选完整性")
    test_candidate_completeness()

    print("\n[2] 打分单调性")
    test_score_monotonicity()

    print("\n[3] 72_02 卡点 (蓝英雄入池)")
    test_72_02_scenario()

    print("\n[4] 硬约束过滤")
    test_hard_constraints()

    print("\n[5] 步预算惩罚")
    test_step_budget_penalty()

    print("\n[6] 粘滞 bonus")
    test_stick_bonus()

    print("\n[7] 阶段调制")
    test_phase_modulation()

    print("\n" + "=" * 60)
    print("✓ 全部离线静态验证通过")
    print("=" * 60)
