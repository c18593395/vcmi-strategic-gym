"""P10 方案实施 (2026-09-15): target_list 价值/威胁加权排序 — Python 旁路打分器.

纯 Python 函数, 零 C++ 重编, 零 obs 维度变更 (3464 冻结铁律).
候选池 = C++ target_list obs[3251:3315] + vmap 静态索引 + obs 英雄段 + obs 城镇段;
打分公式 (方案 §3.2): score = W_type·V + W_win·Δcapture + W_pow·F - W_dist·g(plen) + W_stick·stick - P_phase
硬约束层 (打分前过滤, 全部沿用现机制): BFS 不可达 / guard_blacklist / town_blocked / dyn_blocked / 取兵限次.

接入: ep_runner_one.py 动作 24 段 `--target_chain {legacy,scorer}` 开关, 默认 legacy 零行为变化.
"""
import numpy as np

# obs 段偏移 (strategic_env.py 冻结 3464, 只读不改; 与 ep_runner 同口径)
# ep_runner L613-615: ah=obs[3203], base=128+ah*26, hx=obs[base+2], hy=obs[base+3], hz=obs[base+4]
# 英雄槽 26 字段: 0=hero_id 1=owner 2=x 3=y 4=z(movement?/z) 5=level 6-9=四围 10=total_power
OBS_TL_OFF = 3251      # target_list 8×8
OBS_HERO_OFF = 128     # 英雄段 8×26 (owner/pos/movement/level/四围/total_power/is_garrisoned 等, H.4 全知直读)
OBS_TOWN_OFF = 336     # 城镇段 8×18
OBS_ND_OFF = 3330      # C++ 全图 BFS next_dir[8]
OBS_PAS_OFF = 3211     # 8 方向 passable
# 英雄槽字段索引 (ep_runner 实证): id=0 owner=1 x=2 y=3 z=4 level=5 power=10
H_F_ID, H_F_OWNER, H_F_X, H_F_Y, H_F_Z, H_F_LEVEL, H_F_POW = 0, 1, 2, 3, 4, 5, 10
# 城镇槽字段索引: id=0 owner=1 x=2 y=3 ...(recruit_mask 位 14/15, 见 ep_runner L549/589)
T_F_ID, T_F_OWNER, T_F_X, T_F_Y = 0, 1, 2, 3

# target_list type 枚举 (C++ fill_target_list: 未占矿1/资源堆2/篝火3/宝箱4/宝物5)
TL_MINE = 1
TL_RES = 2
TL_CAMPFIRE = 3
TL_CHEST = 4
TL_RELIC = 5

# 默认权重 (方案 §3.2, 全 argparse 化, 支持网格对照)
DEFAULT_W = dict(
    w_type=1.0,    # 类型基础价值系数
    w_win=1.5,     # 对 1v3 终极目标贡献系数 (蓝英雄/蓝城)
    w_pow=1.0,     # 可打性 logistic 系数
    w_dist=0.5,    # BFS 距离惩罚系数
    w_stick=2.0,   # 目标粘滞 bonus 系数
    margin=20.0,   # 战力差 logistic margin (power_self - power_c - margin)
    temp=30.0,     # logistic 温度
)

# 类型基础价值 V (阶段调制见 §3.2: 蓝英雄>蓝城>未占矿>宝箱/宝物/篝火>资源堆; 已占矿 V=0)
TYPE_VALUE = {
    TL_MINE: 30.0,
    TL_RES: 10.0,
    TL_CAMPFIRE: 12.0,
    TL_CHEST: 20.0,
    TL_RELIC: 25.0,
}

# 蓝英雄/蓝城 特殊价值 (Δcapture 项, 1v3 capture proxy 语义)
BLUE_HERO_VALUE = 100.0   # 每个蓝英雄 +100 (与 ep_runner capture proxy 同口径)
BLUE_TOWN_VALUE = 80.0    # 蓝城 (T06 阶段拉满, 吸收 _t06_direct 特例)
GUARD_VALUE = 45.0        # 守卫 (D3: 价值=价值×可打性, 打得过的守卫 > 打不过的近矿)
OWN_TOWN_VALUE = 35.0     # 回城取兵城 (取兵高频, 战力成长 1v7 核心; 高于资源堆低于矿)

# 可打性 logistic: F = 2σ((log power_self − log power_c − margin)/temp) − 1 ∈ [-1, 1]
# 打不过 (power_c >> power_self) → F≈−1 强负 (不剔除, 兵力成长后自然回升)


def _logistic(x):
    return 1.0 / (1.0 + float(np.exp(-x)))


def _log1p_pos(x):
    """安全 log1p (x≥0). x<0 返 0 (防御)."""
    x = max(0.0, float(x))
    return float(np.log1p(x))


def power_feasibility(power_self, power_c, w):
    """可打性 F ∈ [-1,1]. 蓝英雄/守卫共用 (方案 §3.2).
    power_self < power_c → F 偏负 (打不过, 候选降权但不剔除);
    power_self > power_c + margin → F→+1 (稳赢, 强正).
    """
    if power_c <= 0:
        return 1.0  # 无战力目标 (资源堆/篝火) 全可打
    d = _log1p_pos(power_self) - _log1p_pos(power_c) - w["margin"]
    return 2.0 * _logistic(d / max(1e-6, w["temp"])) - 1.0


def type_value(phase, ttype, mine_taken, c):
    """类型基础价值 V (方案 §3.2): 蓝英雄>蓝城>未占矿>宝箱/宝物/篝火>资源堆; 已占矿 V=0 (D5)."""
    if c.get("is_blue_hero"):
        return BLUE_HERO_VALUE
    if c.get("is_blue_town"):
        return BLUE_TOWN_VALUE if phase == "capture" else BLUE_TOWN_VALUE * 0.5
    if c.get("is_guard"):
        return GUARD_VALUE
    if c.get("is_own_town"):
        return OWN_TOWN_VALUE
    base = TYPE_VALUE.get(ttype, 5.0)
    if ttype == TL_MINE and mine_taken:
        return 0.0
    if phase == "capture" and ttype == TL_MINE:
        return base * 0.5
    return base


def candidate_power_c(c, power_self):
    """候选目标战力近似 (方案 §3.2 可打性项).
    资源/矿/城 power_c=0 (全可打); 蓝英雄取 total_power 直读 (H.4 全知);
    守卫无静态读值 — target_list 的 log2(guard+1) 只限 8 格近邻, 远守卫/蓝城近似 half-self.
    """
    if c.get("is_blue_hero"):
        return c.get("power_c", 0.0)
    if c.get("is_guard") or c.get("is_blue_town"):
        return max(0.0, power_self * 0.5)
    return 0.0


def score_candidates(obs, hx, hy, hz, power_self,
                     mine_taken, town_blocked, town_visited,
                     guard_blacklist, dyn_blocked,
                     phase,
                     w, mapname=None, current_target=None, stall_count=0,
                     guards=None, bfs_full_dir=None,
                     own_town_limit=False, step_budget=0):
    """统一打分排序器 (方案 §3). 返回 [(score, c, meta)] 降序.

    c = 候选 dict: pos=(tx,ty,tz) / type / tl_idx / man / tl_dist /
        is_blue_hero / is_blue_town / is_guard / is_own_town / power_c
    meta = dict(score, plen, bfs_dir, V, F, man, tl_idx, power_c)

    候选池: C++ target_list (矿/资源/篝火/宝箱/宝物, top-8 截断已知缺陷 D1/D2)
          + obs 蓝英雄段 (D4) + obs 蓝城段 (D1) + obs 己方取兵城 + vmap 静态守卫 (D3).
    硬约束层 (打分侧过滤): 空槽 / z 层 / guard_blacklist / dyn_blocked /
        town_blocked / 取兵限次 / man>30 (防跨图) / BFS 不可达.
    bfs_full_dir + mapname 均非 None 时按 BFS 可达过滤 (守卫格/蓝英雄格除外 — passable=0 走贴脸).
    """
    w = {**DEFAULT_W, **(w or {})}
    _bl = set(guard_blacklist or ())
    _db = set(dyn_blocked or ())
    tl = np.asarray(obs[OBS_TL_OFF:OBS_TL_OFF + 64], dtype=np.float32).reshape(8, 8)

    cands = []
    # --- 候选 1: C++ target_list (矿/资源/篝火/宝箱/宝物) ---
    for i in range(8):
        t = tl[i]
        if t[5] <= 0:  # dist 无值 → 空槽
            continue
        ttype = int(t[0])
        tx, ty, tz = int(t[2]), int(t[3]), int(t[4])
        if tz != hz:
            continue
        if (tx, ty) in _bl or (tx, ty) in _db:
            continue
        man = abs(tx - hx) + abs(ty - hy)
        cands.append({
            "pos": (tx, ty, tz), "type": ttype, "tl_idx": i,
            "man": man, "tl_dist": int(t[5]), "guard_pow": int(t[6]),
            "is_blue_hero": False, "is_blue_town": False, "is_guard": False, "is_own_town": False,
            "power_c": 0.0,  # 资源/矿无战力, 可打性恒 +1
        })

    # --- 候选 2: 蓝英雄 (obs 英雄段 owner≠0 且 alive, D4 修复核心) ---
    hero_seg = np.asarray(obs[OBS_HERO_OFF:OBS_HERO_OFF + 8 * 26], dtype=np.float32).reshape(8, 26)
    for h in hero_seg:
        hid = int(h[H_F_ID])
        owner = int(h[H_F_OWNER])
        if hid <= 0 or owner == 0:  # 空槽 / 己方英雄
            continue
        btx, bty, bz = int(h[H_F_X]), int(h[H_F_Y]), int(h[H_F_Z])
        if bz != hz:
            continue
        if btx <= 0 and bty <= 0:
            continue
        if (btx, bty) in _bl or (btx, bty) in _db:
            continue
        bpow = float(h[H_F_POW]) if len(h) > H_F_POW else 0.0
        man = abs(btx - hx) + abs(bty - hy)
        cands.append({
            "pos": (btx, bty, bz), "type": "blue_hero", "tl_idx": -1,
            "man": man, "tl_dist": 0, "guard_pow": int(np.log2(max(1.0, bpow))),
            "is_blue_hero": True, "is_blue_town": False, "is_guard": False, "is_own_town": False,
            "power_c": bpow,
        })
    # --- 候选 3: 蓝城 (obs 城镇段 owner=1, D1/D4 修复: T06 阶段 V 拉满) ---
    town_seg = np.asarray(obs[OBS_TOWN_OFF:OBS_TOWN_OFF + 8 * 18], dtype=np.float32).reshape(8, 18)
    for t in town_seg:
        tid = int(t[T_F_ID])
        towner = int(t[T_F_OWNER])
        if tid <= 0 or towner != 1:  # 只取蓝城 (owner=1), 跳过空槽
            continue
        btx, bty = int(t[T_F_X]), int(t[T_F_Y])
        if btx <= 0 and bty <= 0:  # 空城镇槽
            continue
        if town_blocked or town_visited:
            break  # 本局已 block/visited → 整个蓝城候选类剔除
        if (btx, bty) in _db:
            continue
        man = abs(btx - hx) + abs(bty - hy)
        cands.append({
            "pos": (btx, bty, hz), "type": "blue_town", "tl_idx": -1,
            "man": man, "tl_dist": 0, "guard_pow": 0,
            "is_blue_hero": False, "is_blue_town": True, "is_guard": False, "is_own_town": False,
            "power_c": 0.0,
        })

    # --- 候选 4: 回城取兵城 (obs 城镇段 owner=0 且 recruit_mask≠0, 1v7 战力成长核心) ---
    for t in town_seg:
        tid = int(t[T_F_ID])
        towner = int(t[T_F_OWNER])
        if tid <= 0 or towner != 0:  # 只取己方城
            continue
        btx, bty = int(t[T_F_X]), int(t[T_F_Y])
        if btx <= 0 and bty <= 0:
            continue
        # recruit_mask 非零位 (field 14/15 位或, 同 ep_runner L549/589 口径)
        rm = int(t[14]) | int(t[15]) if len(t) > 15 else 0
        if rm <= 0:
            continue
        if own_town_limit:  # T06 限次 2 硬上限 (ep_runner 状态机), 超限时整类剔除
            continue
        if (btx, bty) in _db:
            continue
        man = abs(btx - hx) + abs(bty - hy)
        if man <= 0 or man > 25:  # 取兵常规行为: 贴脸留给 visit 窗, 跨图不入池
            continue
        cands.append({
            "pos": (btx, bty, hz), "type": "own_town", "tl_idx": -1,
            "man": man, "tl_dist": 0, "guard_pow": 0,
            "is_blue_hero": False, "is_blue_town": False, "is_guard": False, "is_own_town": True,
            "power_c": 0.0,
        })

    # --- 候选 5: 守卫 (vmap 静态 get_guards, D3: 可打性×价值, 非硬编码恒优先) ---
    if guards:
        for g in guards:
            gx, gy, gz = g[0], g[1], g[2]
            if gz != hz:
                continue
            if (gx, gy) in _bl:
                continue
            man = abs(gx - hx) + abs(gy - hy)
            if man == 0 or man > 30:  # 太远守卫不入池 (防跨图烧步); 贴脸 (man=0) 留给战斗/visit 检测
                continue
            cands.append({
                "pos": (gx, gy, gz), "type": "guard", "tl_idx": -1,
                "man": man, "tl_dist": 0, "guard_pow": 0,
                "is_blue_hero": False, "is_blue_town": False, "is_guard": True, "is_own_town": False,
                "power_c": 0.0,
            })

    if not cands:
        return []

    # --- 打分 + 硬约束过滤 (方案 §3.2/§3.3) ---
    scored = []
    for c in cands:
        _cx, _cy, _cz = c["pos"]
        # g(plen): BFS 真实路径 (bfs_full_dir 非 None); 守卫格/蓝英雄格 passable=0 不入 BFS
        # (贴脸 8 邻直接触发战斗, 与 legacy move_guard_target 机制一致), 距离用曼哈顿近似
        bfs_dir = None
        bfs_plen = None
        if bfs_full_dir is not None and mapname is not None and not (c["is_guard"] or c["is_blue_hero"]):
            _dir, _plen = bfs_full_dir(mapname, hx, hy, _cx, _cy, blocked=(_bl | _db) - {(hx, hy)})
            if _dir is None:
                continue  # 不可达不入池 (方案 §3.3 硬约束)
            bfs_dir, bfs_plen = _dir, _plen
        g = bfs_plen if bfs_plen is not None else c["man"]
        V = type_value(phase, c["type"], mine_taken, c)
        # 经济期远目标衰减: g>50 的终极目标 (蓝英雄/蓝城) 大幅降 V, 避免 w_win 无条件下拉
        # (修复: T05 36X36 step 28 蓝英雄 plen=64 F=-0.33 碾压 200 步跑满 r=-11.3)
        if phase == "economy" and g > 50 and (c["is_blue_hero"] or c["is_blue_town"]):
            V = V * 0.2
        # Δcapture: 1v3 蓝英雄/蓝城 终极目标贡献 (蓝英雄最高, 蓝城 0.8 系数)
        delta_cap = 1.0 if c["is_blue_hero"] else (0.8 if c["is_blue_town"] else 0.0)
        # F: 可打性 (logistic 战力差) — 蓝英雄直读 total_power; 守卫/蓝城 half-self 近似; 资源类恒 +1
        pc = candidate_power_c(c, power_self)
        F = power_feasibility(power_self, pc, w) if pc > 0 else 1.0
        # stick: 粘滞 bonus (当前目标未 stall 时强化保持)
        stick = 1.0 if (current_target is not None and
                        (current_target[0] == _cx and current_target[1] == _cy)
                        and stall_count < 6) else 0.0
        # P_phase: 阶段错配惩罚 (economy 窗打蓝英雄/蓝城 → 罚; capture 阶段打资源堆 → 罚)
        if phase == "economy" and (c["is_blue_hero"] or c["is_blue_town"]):
            p_phase = 10.0  # 经济窗先不碰终极目标
        elif phase == "capture" and c["type"] in (TL_RES, TL_CAMPFIRE):
            p_phase = 5.0
        else:
            p_phase = 0.0
        # 步预算惩罚: 剩余步数容不下往返的远候选加罚 (方案 §3.2 "plen 预算惩罚")
        budget_pen = 0.0
        if step_budget > 0 and g > step_budget * 0.5:
            budget_pen = (g - step_budget * 0.5) * 0.2

        score = (w["w_type"] * V
                 + w["w_win"] * delta_cap * V
                 + w["w_pow"] * F * (V + 20.0)
                 - w["w_dist"] * g
                 + w["w_stick"] * stick
                 - p_phase
                 - budget_pen)
        scored.append((score, c, dict(score=score, plen=g, bfs_dir=bfs_dir, V=V, F=F,
                                      man=c["man"], tl_idx=c.get("tl_idx", -1),
                                      power_c=pc, delta_cap=delta_cap, stick=stick,
                                      p_phase=p_phase, budget_pen=budget_pen)))

    scored.sort(key=lambda x: -x[0])
    return scored


def pick_from_scored(scored):
    """从打分结果挑头名 (方案 §3.3 硬约束已在 score_candidates 打分侧过滤).

    返回 (pick, runner_up) 或 (None, None).
    pick = dict(pos=(tx,ty,tz), ttype, tl_idx, is_blue_hero, is_blue_town, is_guard,
                is_own_town, meta) — meta 含 score/plen/V/F/man/tl_idx/bfs_dir.
    ttype: 枚举 int (target_list 5 类) / "blue_hero" / "blue_town" / "guard" / "own_town".
    """
    if not scored:
        return None, None
    _s, c, meta = scored[0]
    runner_up = scored[1] if len(scored) > 1 else None
    pick = dict(
        pos=c["pos"], ttype=c["type"], tl_idx=c.get("tl_idx", -1),
        is_blue_hero=c["is_blue_hero"], is_blue_town=c["is_blue_town"],
        is_guard=c["is_guard"], is_own_town=c["is_own_town"],
        meta=meta,
    )
    return pick, runner_up
