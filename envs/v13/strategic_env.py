# =============================================================================
# strategic_env.py — VCMI 战略层 RL 环境 (gymnasium.Env)
#
# 基于冒险 API (adventure_wait/act) 实现红蓝自博弈训练。
# 观测：StrategicState 结构体 (ctypes 直读 libmlclient.so 的 g_strategic_state)
# 动作：Discrete(25) — 8方向移动 + 交互 + 下一英雄 + 结束回合 + 分兵/合兵/换兵/招兵/建造/驻守/招募英雄/高层移动
# 奖励：资源变化 + 领地扩张 + 英雄经验 + 胜利
# =============================================================================

import ctypes
import os
import threading
import time
from typing import Optional, Dict, Any

import gymnasium as gym
import numpy as np

# 09-23 路径环境化: 默认路径由环境变量派生, 不再硬编码用户名/绝对路径。
# 以 administrator 运行时 expanduser("~") 解析结果与原硬编码值逐字一致;
# 以 root 运行脚本 (批转/复测) 请显式设置 VCMI_NATIVE_DIR / VCMI_WORKSPACE_DIR。
VCMI_NATIVE_DIR = os.environ.get("VCMI_NATIVE_DIR") or os.path.expanduser("~/vcmi-native")
VCMI_WORKSPACE_DIR = os.environ.get("VCMI_WORKSPACE_DIR") or os.path.expanduser("~/vcmi-workspace")
DEFAULT_MLCLIENT = os.path.join(VCMI_NATIVE_DIR, "rel", "bin", "libmlclient.so")
DEFAULT_TERRAIN_GRID = os.path.join(VCMI_WORKSPACE_DIR, "terrain_grid.bin")

# Set RTLD_GLOBAL for ALL subsequent dlopen calls
import sys as _sys
_ctypes = __import__("ctypes")
_sys.setdlopenflags(_sys.getdlopenflags() | _ctypes.RTLD_GLOBAL)

from ..util import log
# Preload libmlclient.so with RTLD_GLOBAL so dlsym finds our version first
import os as _os
_ctypes.CDLL(_os.environ.get("STRATEGIC_STATE_LIB", DEFAULT_MLCLIENT), mode=_ctypes.RTLD_GLOBAL)
from ...connectors.rel import connector_v13

# 从 strategic_reader.py 导入 ctypes 结构体
# (位于项目根目录，提供 StrategicState ctypes 绑定)
try:
    # 尝试直接导入（从根目录运行时）
    import strategic_reader as _sr
except ImportError:
    # 通过 sys.path 回退
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "strategic_reader",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "strategic_reader.py")
    )
    _sr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(spec.name)

StrategicState = _sr.StrategicState
StrategicPlayer = _sr.StrategicPlayer
StrategicHero = _sr.StrategicHero
StrategicTown = _sr.StrategicTown

TRACE = os.getenv("VCMIGYM_DEBUG", "0") == "1"
MAXLEN = 80

# =============================================================================
# NK2 估值函数 (Phase I.1 — 移植自 PriorityEvaluator.cpp)
# =============================================================================

# 矿类型 → 资源价值权重 (源自 NK2 getResourcesGoldReward + getCombinedResourceRequirementStrength)
# type: 0=unknown 1=wood(sawmill) 2=mercury 3=ore(iron) 4=sulfur 5=crystal 6=gems 7=gold
_MINE_TYPE_WEIGHT = {
    0: 0.0,   # unknown
    1: 0.15,  # wood — 基础资源, 需求中等
    2: 0.40,  # mercury — 稀有资源
    3: 0.15,  # ore — 基础资源
    4: 0.40,  # sulfur — 稀有资源
    5: 0.40,  # crystal — 稀有资源
    6: 0.40,  # gems — 稀有资源
    7: 0.25,  # gold — 直接收入, 中等价值
}

# 城镇建筑位 → fort 等级估算 (buildings bitmask 中 fort/citadel/castle 的位)
# VCMI building IDs: TOWN_HALL=0, CITY_HALL=1, CAPITOL=2, FORT=6, CITADEL=7, CASTLE=8
_FORT_BIT = 6
_CITADEL_BIT = 7
_CASTLE_BIT = 8

def nk2_state_value(state) -> float:
    """从 StrategicState 计算全局状态价值 (NK2 估值移植)
    
    源自 PriorityEvaluator.cpp:
    - getStrategicalValue (矿/城/英雄)
    - getResourcesGoldReward (资源金币等价)
    - getArmyReward (军力价值)
    - enemyHeroDangerRatio (敌方威胁)
    
    返回: 标量状态价值, 步间差分用作奖励塑形
    """
    value = 0.0
    
    # --- 1. 资源价值 (己方玩家 P0) ---
    # NK2: getResourcesGoldReward: gold=1:1, 非金=amount×100
    # 归一化: gold×0.001 + raw×0.01 + rare×0.05
    if state.player_count >= 1:
        p0 = state.players[0]
        # 资源不加: wood/ore 被动收集每步正漂移, 淹没真正信号
        # value += (p0.wood + p0.ore) * 0.008
        # value += (p0.mercury + p0.sulfur + p0.crystal + p0.gems) * 0.03
    
    # --- 2. 矿价值 (己方矿) ---
    # NK2: getStrategicalValue(MINE) = 1.0 + getCombinedResourceRequirementStrength(res)
    # 简化: 固定权重按矿类型
    for i in range(state.mine_count):
        m = state.mines[i]
        if m.owner == 0:  # 己方矿
            w = _MINE_TYPE_WEIGHT.get(m.type, 0.2)
            value += 2.5 + w * 5  # 5x 权重: 占矿=+3.5~5.0 奖励信号
    
    # --- 3. 城镇价值 ---
    # NK2: getStrategicalValue(TOWN):
    #   己方: min(1.0, sqrt(armyGrowth/40000)) + min(0.3, dailyIncome/10000)
    #   敌方: 首都1.5, Castle1.4, Citadel1.2, Fort1.0, 无Fort0.8
    # 5x 权重: 占城=+10~15 奖励信号
    for ti in range(8):
        t = state.towns[ti]
        if t.id == 0:
            continue
        if t.owner == 0:  # 己方城镇
            tv = 10.0  # 5x 基础城镇价值 (占城=+10 信号)
            tv += min(2.5, t.gold_income * 0.0005)  # 收入权重 (cap at 2.5)
            # fort 等级奖励 (从 buildings bitmask 解码)
            if t.buildings & (1 << _CASTLE_BIT):
                tv += 3.0
            elif t.buildings & (1 << _CITADEL_BIT):
                tv += 2.0
            elif t.buildings & (1 << _FORT_BIT):
                tv += 1.0
            value += tv
        # 敌方城镇: 不直接加值, 通过 conquest 差分 (占领时 state_value 跳变)
    
    # --- 3.5 守卫接近梯度 (2026-08-27 方案A) ---
    # target_list 行: [type,idx,x,y,z,dist,power(log2),flags]; power>0 = 目标带守卫
    # Φ_guard = -w × min_dist → 每接近守卫 1 格势差 +w (净正, 压过 -0.1 步罚)
    # 守卫清除后该项消失 → 正跳变 (+w×d) 与 +100 战斗事件叠加
    # 系数 09-20 降权: -0.5→-0.15 — T7.8 大负局实锤: 绕怪 dist 暂增被 -0.5×dist 重罚
    # (绕 30 格 = -15 势能坑, 且与 A3 避怪直接对抗: 模型被训练成"宁可踩怪也别绕");
    # -0.15 保留接近梯度信号但绕怪代价可承受 (30 格 = -4.5, 一次占矿 +30 轻松覆盖)。
    guard_d = None
    for _gi in range(8):
        _row = state.target_list[_gi]
        if _row[0] > 0 and _row[6] > 0:
            _d = _row[5]
            guard_d = _d if guard_d is None else min(guard_d, _d)
    if guard_d is not None:
        value += -0.15 * guard_d

    # --- 4. 军力价值 (己方英雄) ---
    # NK2: getArmyReward = creature.getAIValue() × count
    # 军力本身不加 value: 招募每步增长, 产生正漂移
    # 但保留 our_power 供威胁比率计算
    our_power = 0
    for hi in range(8):
        h = state.heroes[hi]
        if h.id >= 0 and h.owner == 0:
            our_power += h.total_power
    
    # --- 5. 敌方威胁惩罚 ---
    # NK2: enemyHeroDangerRatio = enemyDanger / ourStrength
    # enemy_threat[0..6] 是每个敌方玩家的威胁值
    enemy_power = 0
    for i in range(7):
        enemy_power += state.enemy_threat[i]
    if our_power > 0:
        threat_ratio = enemy_power / (our_power + 1.0)
        value -= min(2.0, threat_ratio * 0.5)  # cap at -2.0
    
    # --- 6. 胜利/失败 ---
    if state.game_over == 1:
        value += 50.0  # 红方胜利
    elif state.game_over == 2:
        value -= 50.0  # 红方失败
    
    return value

# =============================================================================
# 常量
# =============================================================================

# 动作空间
MOVE_RIGHT = 0
MOVE_DOWN_RIGHT = 1
MOVE_DOWN = 2
MOVE_DOWN_LEFT = 3
MOVE_LEFT = 4
MOVE_UP_LEFT = 5
MOVE_UP = 6
MOVE_UP_RIGHT = 7
INTERACT = 8       # 拾取/对话/攻击
NEXT_HERO = 9      # 切换到下一英雄
END_TURN = 10      # 结束当前回合
# H.6: 动作 11-24 (v1 引擎侧解析最近目标, 详见 docs/H6_reasonix_task.md / docs/动作空间设计文档.md §1.2)
SPLIT_1OF3 = 11    # 分 1/3 兵力给最近友方英雄
SPLIT_1OF2 = 12    # 分 1/2 兵力给最近友方英雄
SPLIT_ALL = 13     # 全部兵力给最近友方英雄
MERGE_FROM = 14    # 从最近友方英雄合并全部兵力
SWAP_ARMY = 15     # 与最近友方英雄交换兵力
RECRUIT_1 = 16     # 最近己方城镇招最低级可招兵×1
RECRUIT_2 = 17     # 最近己方城镇招最高级可招兵×1
RECRUIT_3 = 18     # 最近己方城镇全部可招兵各×1
BUILD_1 = 19       # 最近己方城镇建大厅链第一个未建
BUILD_2 = 20       # 最近己方城镇建兵种链第一个未建
BUILD_3 = 21       # 最近己方城镇建防御链第一个未建
GARRISON = 22      # 当前英雄驻守最近己方城镇
RECRUIT_HERO = 23  # 最近己方城镇招募新英雄
MOVE_TO = 24       # 高层移动: 走到最近可交互对象

N_ACTIONS = 25

# 观测向量维度 (OBS schema v3: 8+120+208+144+675+2048+8+8+32+64+7+4+4+134 = 3464)
OBS_DIM = 3464

# StrategicState 最大实体数
MAX_PLAYERS = 8
MAX_HEROES = 8
MAX_TOWNS = 8

# OBS schema v3 段常量 (与 strategic_reader.py / C 头一致)
LOCAL_WIN = getattr(_sr, "LOCAL_WIN", 15)      # local_tiles 窗口边长
LOCAL_CH = getattr(_sr, "LOCAL_CH", 3)         # v3: 通道数
GLOBAL_GRID = getattr(_sr, "GLOBAL_GRID", 32)  # global_explored 网格边长
MAX_LEVELS = getattr(_sr, "MAX_LEVELS", 2)     # 地图层数
NAV_SIZE = getattr(_sr, "NAV_SIZE", 32)
TARGET_LIST = getattr(_sr, "TARGET_LIST", 8)
TARGET_DIM = getattr(_sr, "TARGET_DIM", 8)
ENEMY_THREAT = getattr(_sr, "ENEMY_THREAT", 7)
BATTLE_PRED = getattr(_sr, "BATTLE_PRED", 4)
EVENTS_SIZE = getattr(_sr, "EVENTS_SIZE", 4)
RESERVED_SIZE = getattr(_sr, "RESERVED_SIZE", 134)
TERRAIN_GRID_SIZE = 21
TERRAIN_GRID_CHANNELS = 4
TERRAIN_GRID_TOTAL = TERRAIN_GRID_SIZE * TERRAIN_GRID_SIZE * TERRAIN_GRID_CHANNELS  # 1764


# =============================================================================
# 辅助函数
# =============================================================================

def tracelog(func, maxlen=MAXLEN):
    """调试日志装饰器"""
    if not TRACE:
        return func

    def wrapper(*args, **kwargs):
        this = args[0]
        this.logger.debug("Begin: %s (args=%s, kwargs=%s)" % (
            func.__name__, args[1:], log.trunc(repr(kwargs), maxlen)))
        result = func(*args, **kwargs)
        this.logger.debug("End: %s (return %s)" % (
            func.__name__, log.trunc(repr(result), maxlen)))
        return result

    return wrapper


def _read_strategic_state(lib_path: str = None):
    """从 libmlclient.so 读取 g_strategic_state，返回 StrategicState 实例或 None"""
    if lib_path is None:
        # 默认路径由 VCMI_NATIVE_DIR 派生 — 可通过环境变量 STRATEGIC_STATE_LIB 覆盖
        lib_path = os.environ.get(
            "STRATEGIC_STATE_LIB",
            DEFAULT_MLCLIENT
        )

    if not os.path.exists(lib_path):
        # 尝试备用路径（直接从 WSL 内部）
        wsl_path = DEFAULT_MLCLIENT
        lib_path = os.environ.get("STRATEGIC_STATE_LIB") or wsl_path

    try:
        libml = ctypes.CDLL(lib_path)
        ptr = ctypes.c_void_p.in_dll(libml, "g_strategic_state")
        if not ptr.value:
            return None
        return StrategicState.from_address(ptr.value)
    except Exception:
        return None


def _strategic_state_to_obs(state: StrategicState) -> np.ndarray:
    """将 StrategicState ctypes 结构体展平为 1D numpy 观测向量 (OBS schema v3, 3456 维)

    布局 (索引从 0 开始):
      [0:8]      global          day,week,month,current_player,map_w,map_h,has_underground,player_count
      [8:128]    players         8 x 15 = 120
      [128:336]  heroes          8 x 26 = 208
      [336:480]  towns           8 x 18 = 144
      [480:1155] local window    15 x 15 x 3 = 675 (ch 外层: 0=可通行 1=对象类型 2=守卫战力)
      [1155:3203] global explored 32 x 32 x 2 = 2048, 先 z=0 层再 z=1 层
      [3203:3211] active_hero    obs[3203]=state.active_hero, 其余保留 0
      [3211:3219] passable       8 (不再在末尾, 固定偏移)
      [3219:3251] nav            32
      [3251:3315] target_list    64 (8x8, v2 启用)
      [3315:3322] enemy_threat   7
      [3322:3326] battle_pred    4
      [3326:3330] events         4
      [3330:3464] reserved       134
    """
    obs = np.zeros(OBS_DIM, dtype=np.float32)
    idx = 0

    # --- Global (8) ---
    obs[idx] = state.day;             idx += 1
    obs[idx] = state.week;            idx += 1
    obs[idx] = state.month;           idx += 1
    obs[idx] = state.current_player;  idx += 1
    obs[idx] = state.map_width;       idx += 1
    obs[idx] = state.map_height;      idx += 1
    obs[idx] = state.has_underground;  idx += 1
    obs[idx] = state.player_count;    idx += 1

    # --- Players (8 * 15 = 120) ---
    for pi in range(MAX_PLAYERS):
        p = state.players[pi]
        if pi < state.player_count:
            obs[idx] = p.color;        idx += 1
            obs[idx] = p.human;        idx += 1
            obs[idx] = p.gold;         idx += 1
            obs[idx] = p.wood;         idx += 1
            obs[idx] = p.mercury;      idx += 1
            obs[idx] = p.ore;          idx += 1
            obs[idx] = p.sulfur;       idx += 1
            obs[idx] = p.crystal;      idx += 1
            obs[idx] = p.gems;         idx += 1
            obs[idx] = p.hero_count;   idx += 1
            obs[idx] = p.town_count;   idx += 1
            obs[idx] = p.alive;        idx += 1
            obs[idx] = p.total_power;  idx += 1
            obs[idx] = p.weekly_income; idx += 1
            obs[idx] = p.relation_to_me; idx += 1
        else:
            idx += 15  # 空槽位保持 0

    # --- Heroes (8 * 26 = 208) ---
    _HERO_FIELDS = 26
    for hi in range(MAX_HEROES):
        h = state.heroes[hi]
        if h.id >= 0:
            obs[idx] = h.id;           idx += 1
            obs[idx] = h.owner;        idx += 1
            obs[idx] = h.pos_x;        idx += 1
            obs[idx] = h.pos_y;        idx += 1
            obs[idx] = h.pos_z;        idx += 1
            obs[idx] = h.movement;     idx += 1
            obs[idx] = h.max_movement; idx += 1
            obs[idx] = h.level;        idx += 1
            obs[idx] = h.attack;       idx += 1
            obs[idx] = h.defense;      idx += 1
            obs[idx] = h.power;        idx += 1
            obs[idx] = h.knowledge;    idx += 1
            obs[idx] = h.mana;         idx += 1
            obs[idx] = h.max_mana;     idx += 1
            obs[idx] = h.exp;          idx += 1
            # army (7 slots)
            for ai in range(7):
                obs[idx] = h.army_count[ai]; idx += 1
            obs[idx] = h.in_battle;    idx += 1
            obs[idx] = h.total_power;  idx += 1
            obs[idx] = h.is_garrisoned; idx += 1
            obs[idx] = h.has_commander; idx += 1
        else:
            idx += _HERO_FIELDS  # 空槽位保持 0

    # --- Towns (8 * 18 = 144) ---
    _TOWN_FIELDS = 18
    for ti in range(MAX_TOWNS):
        t = state.towns[ti]
        if t.id != 0:
            obs[idx] = t.id;           idx += 1
            obs[idx] = t.owner;        idx += 1
            obs[idx] = t.pos_x;        idx += 1
            obs[idx] = t.pos_y;        idx += 1
            obs[idx] = t.pos_z;        idx += 1
            obs[idx] = t.buildings;    idx += 1
            # garrison (7 slots)
            for ai in range(7):
                obs[idx] = t.garrison[ai]; idx += 1
            obs[idx] = t.gold_income;  idx += 1
            obs[idx] = t.recruit_mask_lo; idx += 1
            obs[idx] = t.recruit_mask_hi; idx += 1
            obs[idx] = t.build_mask_lo;   idx += 1
            obs[idx] = t.build_mask_hi;   idx += 1
        else:
            idx += _TOWN_FIELDS  # 空槽位保持 0

    # --- Local window (15*15*3=675) — ch 外层, 行主序 ---
    for ch in range(LOCAL_CH):
        for li in range(LOCAL_WIN):
            row = state.local_tiles[ch][li]
            for lj in range(LOCAL_WIN):
                obs[idx] = row[lj]
                idx += 1

    # --- Global explored (32 * 32 * 2 = 2048) — 先 z=0 层再 z=1 层 ---
    for z in range(MAX_LEVELS):
        layer = state.global_explored[z]
        for gy in range(GLOBAL_GRID):
            row = layer[gy]
            for gx in range(GLOBAL_GRID):
                obs[idx] = row[gx]
                idx += 1

    # --- Active hero (8) — 固定偏移 3203 ---
    obs[3203] = state.active_hero

    # --- Passability (8) — 固定偏移 3211 (不再在末尾!) ---
    for di in range(8):
        obs[3211 + di] = state.passable[di]

    # --- Nav (32) — 3219:3251 ---
    for i in range(NAV_SIZE):
        obs[3219 + i] = state.nav[i]

    # --- Target list (64) — 3251:3315 ---
    for i in range(TARGET_LIST):
        for j in range(TARGET_DIM):
            obs[3251 + i * TARGET_DIM + j] = state.target_list[i][j]

    # --- Enemy threat (7) — 3315:3322 ---
    for i in range(ENEMY_THREAT):
        obs[3315 + i] = state.enemy_threat[i]

    # --- Battle pred (4) — 3322:3326 ---
    for i in range(BATTLE_PRED):
        obs[3322 + i] = state.battle_pred[i]

    # --- Events (4) — 3326:3330 ---
    for i in range(EVENTS_SIZE):
        obs[3326 + i] = state.events[i]

    # --- Reserved (134) — 3330:3464 ---
    # I.2: reserved[0..7] = next_dir[8] (C++ BFS 全图寻路第一步方向, -1=不可达)
    # reserved[8..15] = diagnostics (hx,hy,hz,W,H,reserved,next_dir_t0,explored)
    for i in range(16):
        obs[3330 + i] = state.reserved[i]

    # Phase I.4: terrain_grid (独立存储, 不进 obs 向量)

    # --- 2026-08-16 H.8 修复: 大数值字段归一化 (数值爆炸根因) ---
    # 2689 时代 obs max=6410 可训 (C8.5 vloss=1349 正常); v3 新增未归一化大字段:
    #   gold 74万 / total_power 7.8万 / weekly_income 1.7万 / enemy_threat 11万
    # 直接喂 Linear → logits 300-1700 爆炸 → vloss 1e4+ / 动作坍缩 (build_mask 2e9 已单列处理)
    # 处理1: build_mask_lo/hi (bitmask, 全置位≈2.1e9) ÷2^31 → [0,1), 保留位语义
    # 处理2: 数值型大字段 log1p 压缩 (0→0, 1e6→13.8), 与 bc_train.py 旧数据对齐
    _BM_COLS = [336 + ti * _TOWN_FIELDS + 16 for ti in range(MAX_TOWNS)] + \
               [336 + ti * _TOWN_FIELDS + 17 for ti in range(MAX_TOWNS)]
    obs[_BM_COLS] /= float(2 ** 31)
    _LOG1P_COLS = []
    for _pi in range(MAX_PLAYERS):  # players: gold(+2), total_power(+12), weekly_income(+13)
        _b = 8 + _pi * 15
        _LOG1P_COLS += [_b + 2, _b + 12, _b + 13]
    for _hi in range(MAX_HEROES):   # heroes: movement(+5), max_movement(+6), exp(+14), total_power(+23)
        _b = 128 + _hi * 26
        _LOG1P_COLS += [_b + 5, _b + 6, _b + 14, _b + 23]
    _LOG1P_COLS += list(range(3315, 3322))  # enemy_threat 7
    _LOG1P_COLS += list(range(3322, 3326))  # battle_pred 4
    obs[_LOG1P_COLS] = np.log1p(np.maximum(obs[_LOG1P_COLS], 0.0))

    return obs


# =============================================================================
# StrategicEnv
# =============================================================================

class StrategicEnv(gym.Env):
    """
    VCMI 冒险地图战略层 RL 环境

    使用 connector_v13.ThreadConnector 的 adventure_wait/act API
    与 VCMI 进程通信，通过 ctypes 读取 StrategicState 结构体获取观测。
    """

    metadata = {"render_modes": ["ansi"], "render_fps": 10}

    # 暴露常量供外部使用
    N_ACTIONS = N_ACTIONS
    OBS_DIM = OBS_DIM
    MAX_PLAYERS = MAX_PLAYERS
    MAX_HEROES = MAX_HEROES
    MAX_TOWNS = MAX_TOWNS

    def __init__(
        self,
        mapname: str = "adventure-A1.vmap",
        seed: Optional[int] = None,
        max_turns: int = 28,
        vcmi_loglevel_global: str = "warn",
        vcmi_loglevel_ai: str = "error",
        vcmienv_loglevel: str = "WARN",
        vcmienv_logtag: str = "StrategicEnv-v1",
        red: str = "Nullkiller2",
        blue: str = "StupidAI",
        red_adventure_ai: str = "MMAI",
        blue_adventure_ai: str = "Nullkiller2",
        red_allow_mlbot: bool = False,
        blue_allow_mlbot: bool = False,
        random_heroes: int = 1,
        boot_timeout: int = 120,
        vcmi_timeout: int = 99999,
        user_timeout: int = 99999,
        libml_path: Optional[str] = None,
        # 对手池模型路径
        red_model_path: str = "",
        blue_model_path: str = "",
        # 奖励系数
        reward_gold_mult: float = 0.0,     # C8.5: 禁被动 gold per-step (100g=+1 导致 END_TURN 坚守: day推进被动收入每步+5~10)
        reward_town_mult: float = 30.0,
        reward_hero_mult: float = 10.0,
        reward_win: float = 200.0,
        reward_step_fixed: float = -1.2,  # 2026-08-25 方案a: -1.5→-1.2 微调 (长局"打赢"收益更可见; 原则 -1.0~-2.0 压制不动)
        reward_explore: float = 0.0,   # 探索奖励: 访问新格子 (C8.5)
        # A+B: 事件奖励 (占矿/打赢战斗/英雄升级)
        reward_mine_mult: float = 10.0,    # 占矿 (owner !=0 → 0)
        reward_battle_mult: float = 100.0, # 打赢战斗 (battle_result 0/2/3 → 1)
        reward_first_win_bonus: float = 100.0,  # 2026-08-25 方案a: 每局首胜额外加成 (治"打赢被步数惩罚稀释")
        reward_level_mult: float = 10.0,   # 英雄升级
        # Phase I.1: NK2 势函数奖励
        use_nk2_shaping: bool = False,     # True = 用 nk2_state_value 差分替代事件奖励
        nk2_shaping_scale: float = 1.0,    # 势函数差分缩放
        random_armies: bool = False,       # 随机军队 (True=用randomArmyValue)
        random_army_min: int = 500,        # 随机军队最低价值
        random_army_max: int = 1000,       # 随机军队最高价值
    ):
        super().__init__()

        # 确保地图名含冒险前缀
        assert any(kw in mapname.lower() for kw in ["s1", "mini", "adventure", "h3m"]), (
            f"Map '{mapname}' must contain 's1', 'mini', or 'adventure' for adventure mode"
        )

        # --- 空间定义 ---
        self.action_space = gym.spaces.Discrete(N_ACTIONS)
        self.observation_space = gym.spaces.Box(
            low=-1e6, high=1e6, shape=(OBS_DIM,), dtype=np.float32
        )

        # --- 参数 ---
        self.mapname = mapname
        self.seed = seed or 0
        self.max_turns = max_turns
        self.render_mode = "ansi"
        self.libml_path = libml_path
        
        # 保存 connector 参数（用于重启）
        self._boot_timeout = boot_timeout
        self._vcmi_timeout = vcmi_timeout
        self._user_timeout = user_timeout
        self._red = red
        self._blue = blue
        self._red_allow_mlbot = red_allow_mlbot
        self._blue_allow_mlbot = blue_allow_mlbot
        self._random_heroes = random_heroes
        self._vcmi_loglevel_global = vcmi_loglevel_global
        self._vcmi_loglevel_ai = vcmi_loglevel_ai

        # --- 日志 ---
        self.logger = log.get_logger(vcmienv_logtag, vcmienv_loglevel)
        self.logger.debug("Initializing StrategicEnv...")

        # --- 奖励配置 ---
        self.reward_gold_mult = reward_gold_mult
        self.reward_town_mult = reward_town_mult
        self.reward_hero_mult = reward_hero_mult
        self.reward_win = reward_win
        # Phase I.1: NK2 势函数模式下大幅降低 step_fixed (必须在赋值前)
        if use_nk2_shaping and reward_step_fixed < -0.5:
            print(f"[NK2] overriding step_fixed {reward_step_fixed} → -0.1 (NK2 shaping mode, 2026-08-25 方案a 微调)", flush=True)
            reward_step_fixed = -0.1
        self.reward_step_fixed = reward_step_fixed
        self.reward_explore = reward_explore
        # A+B: 事件奖励系数
        self.reward_mine_mult = reward_mine_mult
        self.reward_battle_mult = reward_battle_mult
        self.reward_first_win_bonus = reward_first_win_bonus  # 2026-08-25 方案a
        self.reward_level_mult = reward_level_mult
        # Phase I.1: NK2 势函数
        self.use_nk2_shaping = use_nk2_shaping
        self.nk2_shaping_scale = nk2_shaping_scale
        self._visited = set()  # 已访问格子 (探索奖励)
        self._first_win_done = False  # 2026-08-25 方案a: 本局是否已拿首胜加成
        self._random_armies = random_armies
        self._random_army_min = random_army_min
        self._random_army_max = random_army_max

        # --- 创建连接器 ---
        self.connector = connector_v13.ThreadConnector(
            maxlogs=100,
            bootTimeout=boot_timeout,
            vcmiTimeout=vcmi_timeout,
            userTimeout=user_timeout,
            red=red,
            redModel=red_model_path,
            blue=blue,
            blueModel=blue_model_path,
            redAdventureAI=red_adventure_ai,
            blueAdventureAI=blue_adventure_ai,
            mapname=mapname,
            seed=self.seed,
            randomHeroes=random_heroes,
            randomObstacles=0,
            townChance=0,
            warmachineChance=0,
            randomArmies=getattr(self, "_random_armies", False),
            randomArmyValueMin=getattr(self, "_random_army_min", 500),
            randomArmyValueMax=getattr(self, "_random_army_max", 1000),
            randomArmyTargetVar=0,
            tightFormationChance=0,
            randomTerrainChance=0,
            leftVipChance=0,
            rightVipChance=0,
            battlefieldPattern="",
            manaMin=0,
            manaMax=0,
            randomPrimarySkills=0,
            swapSides=0,
            loglevelGlobal=vcmi_loglevel_global,
            loglevelAI=vcmi_loglevel_ai,
            loglevelNetwork="error",
            loglevelStats=vcmi_loglevel_global,
            redAllowMlBot=red_allow_mlbot,
            blueAllowMlBot=blue_allow_mlbot,
            statsMode="disabled",
            statsStorage="-",
            statsPersistFreq=100,
        )
        self.logger.debug("ThreadConnector created")

        # 在主线程初始化 VCMI（SDL 需要主线程）
        self.connector.init()
        self.logger.debug("VCMI init OK (main thread)")

        # --- VCMI 启动 (在后台线程) ---
        self._vcmi_started = False
        self._vcmi_just_started = False  # DummyVecEnv 短路标志
        self._vcmithread = None

        # --- g_strategic_state 读取 ---
        # 启动后由 VCMI 线程填充，这里先初始化
        self._state_cache = None  # 缓存的 StrategicState 指针
        self._libml = None        # ctypes 加载的 libmlclient，用于 atomic 通信

        # --- 回合状态 ---
        self._turn = 0
        self._prev_player0 = {"gold": 0, "towns": 0, "heroes": 0}  # 防御性初始化
        self._prev_player1 = {"gold": 0, "towns": 0, "heroes": 0}
        self._last_state = None   # 上次读取的 StrategicState

        # --- 终止标志 ---
        self._terminated = False
        self._truncated = False
        self._game_over = 0
        self._terrain_grid = np.zeros((TERRAIN_GRID_CHANNELS, TERRAIN_GRID_SIZE, TERRAIN_GRID_SIZE), dtype=np.float32)

    # ------------------------------------------------------------------
    # gymnasium.Env 接口
    # ------------------------------------------------------------------

    @tracelog
    def reset(self, seed=None, options=None):
        """启动 VCMI，等待 yourTurn 回调，返回初始观测"""
        super().reset(seed=seed)

        self._turn = 0
        self._terminated = False
        self._truncated = False
        self._game_over = 0
        self._visited = set()  # 探索奖励: 每局重置
        self._consecutive_endturn = 0  # 2026-08-02: 连续 END_TURN 计数 (防刷底)

        # 启动 VCMI（如果尚未启动）
        self._libml = None  # 清理旧 libml 引用
        self._ensure_vcmi_running()

        # 初始化奖励跟踪基线（必须在 adventure_wait 之前，防止超时跳过）
        self._init_baselines(None)

        # 等待第一个 yourTurn 回调（此时 state_update 已执行）
        self.logger.debug("Waiting for first yourTurn callback...")
        try:
            self._adventure_wait()
        except RuntimeError:
            self.logger.warning("YourTurn timed out — game may have ended")
            obs = np.zeros(OBS_DIM, dtype=np.float32)
            info = {"day": 0, "current_player": -1, "turn": 0}
            info["terrain_grid"] = self._terrain_grid
            return obs, info

        # 读取初始状态（VCMI 已在 process_turn 阻塞，状态已更新）
        state = self._read_state()
        obs = self._build_obs(state)
        self._terrain_grid = self._build_terrain_grid(state)

        # 初始化奖励跟踪基线
        self._init_baselines(state)

        info = {
            "day": state.day if state else 1,
            "current_player": state.current_player if state else 0,
            "turn": self._turn,
        }
        info["terrain_grid"] = self._terrain_grid
        return obs, info

    @tracelog
    def step(self, action: int):
        """
        执行动作，返回 (obs, reward, terminated, truncated, info)

        动作 0-7: 移动方向
        动作 8:    交互 (拾取/对话/攻击)
        动作 9:    切换到下一英雄
        动作 10:   结束回合
        动作 11-24: 分兵/合兵/换兵/招兵/建造/驻守/招募英雄/高层移动 (H.6, 引擎侧解析最近目标)

        顺序: SEND → WAIT → READ
        - SEND: 将上一步决定的 action 发给 VCMI
        - WAIT: 等 VCMI 处理完 action 并进入下一轮 process_turn
        - READ: 此时 state_update 已执行完毕，状态保证为新
        """
        if self._terminated or self._truncated:
            raise RuntimeError("Episode is done. Call reset() first.")

        # 发送动作（VCMI 当前阻塞在 process_turn，立即处理）
        self._send_action(action)

        # 等待 VCMI 处理完 action 并进入下一轮 process_turn
        try:
            self._adventure_wait()
        except RuntimeError as e:
            self.logger.error(f"adventure_wait timed out: {e} — forcing episode end")
            self._terminated = True
            obs = np.zeros(OBS_DIM, dtype=np.float32)
            reward = 0.0
            info = {
                "day": 0,
                "current_player": -1,
                "game_over": 0,
                "turn": self._turn + 1,
                "timeout": True,
            }
            return obs, reward, self._terminated, self._truncated, info

        # 只在 END_TURN 时递增 VCMI 回合计数
        if action == END_TURN:
            self._turn += 1
            self._consecutive_endturn += 1
        else:
            self._consecutive_endturn = 0

        # 读取新状态（VCMI 已执行 state_update，保证为最新）
        state = self._read_state()
        obs = self._build_obs(state)
        self._terrain_grid = self._build_terrain_grid(state)

        # 计算奖励
        reward = self._calc_reward(state)
        # potential-based shaping 终结修正 (09-20 BUG修复): shaping = γΦ(s')-Φ(s) 要求 episode
        # 终止时补 -Φ(s') 终结项 (Φ 终值视为 0), 否则负势残留污染: 绕怪 dist 增大的 -0.5×dist
        # 坑在死亡/截断时无法被回程正势抵消 (实锤: T7.8 大负局 -735×2/-488, 绕怪越远残留越大)。
        self._terminated, self._truncated = self._check_done(state)
        if (self._terminated or self._truncated) and self.use_nk2_shaping:
            reward -= self._prev_nk2_value * self.nk2_shaping_scale
            self._prev_nk2_value = 0.0
        # 2026-08-02: 连续 END_TURN 惩罚 — 第 3 次起每次固定 -5 (C8.5 塌缩刷底无成本根因; 固定值避免 n 递增爆炸 -32889)
        if self._consecutive_endturn >= 3:
            reward -= 5.0

        info = {
            "day": state.day if state else 1,
            "current_player": state.current_player if state else 0,
            "game_over": self._game_over,
            "turn": self._turn,
        }
        info["terrain_grid"] = self._terrain_grid
        if self._terminated or self._truncated:
            self.logger.info(
                f"Episode done: turn={self._turn}, "
                f"terminated={self._terminated}, truncated={self._truncated}, "
                f"game_over={self._game_over}"
            )

        return obs, reward, self._terminated, self._truncated, info

    @tracelog
    def render(self):
        """返回简单文本状态描述"""
        state = self._read_state()
        if not state:
            return "State: None\n"

        lines = []
        lines.append(f"Day {state.day}.{state.week}.{state.month} | "
                     f"Player: P{state.current_player} | "
                     f"Turn: {self._turn}/{self.max_turns}")
        for pi in range(state.player_count):
            p = state.players[pi]
            lines.append(f"  P{pi}: gold={p.gold} wood={p.wood} ore={p.ore} "
                         f"heroes={p.hero_count} towns={p.town_count} "
                         f"alive={p.alive}")

        for hi in range(MAX_HEROES):
            h = state.heroes[hi]
            if h.id >= 0:
                lines.append(f"  H{hi}: id={h.id} owner=P{h.owner} "
                             f"pos=({h.pos_x},{h.pos_y},{h.pos_z}) "
                             f"lvl={h.level} mv={h.movement}/{h.max_movement} "
                             f"army={sum(h.army_count)}")

        return "\n".join(lines) + "\n"

    @tracelog
    def close(self):
        """关闭连接器（非阻塞）"""
        self.logger.info("Closing StrategicEnv...")
        # 后台线程 shutdown，带超时避免卡死
        def _try_shutdown():
            try:
                self.connector.shutdown()
            except Exception:
                pass
        t = threading.Thread(target=_try_shutdown, daemon=True)
        t.start()
        t.join(timeout=3)
        
        if self._vcmithread and self._vcmithread.is_alive():
            self._vcmithread.join(timeout=2)
        self._vcmithread = None
        self._vcmi_started = False
        self._vcmi_just_started = False

        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
            handler.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _ensure_vcmi_running(self):
        """确保 VCMI 已在后台线程启动"""
        if self._vcmi_started:
            self.logger.warning("VCMI already running, call close() first")
            return

        self.logger.debug("Starting VCMI in background thread...")
        self._vcmithread = threading.Thread(
            target=self.connector.start,
            name="StrategicVCMI",
            daemon=True,
        )
        self._vcmithread.start()
        time.sleep(2)
        self._vcmi_started = True
        self._vcmi_just_started = True  # 标记本次启动，供 reset() 短路用
        self.logger.debug("VCMI started")

    def _adventure_wait(self, timeout=None):
        """包装 adventure_wait，通过 ctypes 调用 libmlclient 内的原子变量等待

        不经过 connector（避免跨库函数指针调用崩溃），直接用 ctypes 调用
        adventure_wait_for_turn() 和 adventure_send_action()。
        """
        if timeout is None:
            timeout = min(self._vcmi_timeout, 300)  # R7 fix (2026-09-03): fuse 900→300s — 冻结实测 13min 未触发窗口过长; 正常单步等待 <10s, 300s 余量充足
        self._ensure_libml_loaded()
        if self._libml is None:
            raise RuntimeError("libmlclient.so not loaded")

        # 在后台线程中调用 C 函数（避免 C 层无限循环阻塞 Python）
        import threading as _thr
        result = []
        def _wait():
            try:
                r = self._libml.adventure_wait_for_turn()
                result.append(r)
            except Exception:
                result.append(-3)

        t = _thr.Thread(target=_wait, daemon=True)
        t0 = time.time()
        t.start()
        t.join(timeout)
        
        if not result:
            # 超时 - C 函数仍在循环，忽略它（daemon thread 会在进程结束时退出）
            self.logger.warning(f"adventure_wait timed out after {timeout}s")
            raise RuntimeError(f"adventure_wait timed out after {timeout}s")
        
        r = result[0]
        if r >= 0:
            self.logger.debug(f"yourTurn: player={r} ({time.time()-t0:.1f}s)")
            return
        elif r == -2:
            # H3 fix (2026-09-14): C++ 侧 adventure_wait_for_turn 检测到终局（红方真败
            # 无将无城, yourTurn 不再回调）已刷新终局快照 (game_over=2) → 返回 -2。
            # 静默 return, 让 step() 继续走 _read_state → _build_obs → _calc_reward(-200)
            # → _check_done (terminated), 避免落入下方 else 的 unexpected 分支被 L724 捕获
            # 成 timeout forcing (r=0, 全零 obs, -200 败北信号丢失)。
            self.logger.info(f"adventure_wait terminal: red lost, state refreshed (wait={time.time()-t0:.1f}s)")
            return
        elif r == -3:
            raise RuntimeError("adventure_wait: exception in C call")
        else:
            raise RuntimeError(f"adventure_wait: unexpected return {r}")

    def _send_action(self, action: int):
        """通过 ctypes 向 libmlclient 发送 action"""
        self._ensure_libml_loaded()
        if self._libml is not None:
            # 先把动作写入共享全局变量 g_rl_action（C++ yourTurn 从此读取，不改变 struct 尺寸）
            try:
                g_rl = ctypes.c_int32.in_dll(self._libml, "g_rl_action")
                g_rl.value = int(action)
            except Exception:
                pass
            self._libml.adventure_send_action(int(action))

    def _ensure_libml_loaded(self):
        if self._libml is None:
            # 使用 RTLD_NOLOAD 获取已加载的 libmlclient 实例（VCMI 已加载）
            # 避免 ctypes 创建新实例导致静态变量隔离
            import ctypes.util
            lib_name = DEFAULT_MLCLIENT
            try:
                # 先用 CDLL 加载（如果尚未加载，RTLD_NOLOAD 方式不可靠）
                lib_path = self.libml_path or os.environ.get("STRATEGIC_STATE_LIB",
                    DEFAULT_MLCLIENT)
                if lib_path and os.path.exists(lib_path):
                    self._libml = ctypes.CDLL(lib_path)
                else:
                    self._libml = ctypes.CDLL(lib_name)
                self._libml.adventure_wait_for_turn.restype = ctypes.c_int
            except Exception as e:
                self.logger.error(f"Failed to load libmlclient: {e}")
                self._libml = None

    def _read_state(self) -> Optional[StrategicState]:
        """读取当前的 StrategicState"""
        # 每次读取重新加载库（DBus/nfs 场景下可靠）
        state = _read_strategic_state(self.libml_path)
        if state is not None:
            self._last_state = state
            self._game_over = state.game_over
        return state

    def _build_obs(self, state: Optional[StrategicState]) -> np.ndarray:
        """从 StrategicState 构建观测向量"""
        if state is None:
            return np.zeros(OBS_DIM, dtype=np.float32)
        return _strategic_state_to_obs(state)

    def _build_terrain_grid(self, state: Optional[StrategicState]) -> np.ndarray:
        """从 VCMI_WORKSPACE_DIR/terrain_grid.bin 读取 (21x21x4, uint8 -> float32 CHW)"""
        try:
            import time
            # Wait up to 2s for file to be written (server fills it each turn)
            for attempt in range(20):
                raw = np.fromfile(DEFAULT_TERRAIN_GRID, dtype=np.uint8, count=TERRAIN_GRID_TOTAL)
                nonz = int(np.count_nonzero(raw)) if raw.shape[0] == TERRAIN_GRID_TOTAL else 0
                if raw.shape[0] == TERRAIN_GRID_TOTAL and nonz > 0:
                    print(f"[TERRAIN] Python read OK: {nonz} non-zero at attempt {attempt}", flush=True)
                    break
                time.sleep(0.1)
            else:
                print(f"[TERRAIN] Python read FAILED: shape={raw.shape} nonz={nonz}", flush=True)
            if raw.shape[0] < TERRAIN_GRID_TOTAL:
                return np.zeros((TERRAIN_GRID_CHANNELS, TERRAIN_GRID_SIZE, TERRAIN_GRID_SIZE), dtype=np.float32)
            hwc = raw.reshape(TERRAIN_GRID_SIZE, TERRAIN_GRID_SIZE, TERRAIN_GRID_CHANNELS)
            chw = hwc.transpose(2, 0, 1).astype(np.float32) / 255.0
            return chw
        except Exception:
            return np.zeros((TERRAIN_GRID_CHANNELS, TERRAIN_GRID_SIZE, TERRAIN_GRID_SIZE), dtype=np.float32)

    def _init_baselines(self, state: Optional[StrategicState]):
        """初始化奖励基线值"""
        self._prev_player0 = {"gold": 0, "wood": 0, "mercury": 0, "ore": 0,
                              "sulfur": 0, "crystal": 0, "gems": 0,
                              "towns": 0, "heroes": 0}
        self._prev_player1 = dict(self._prev_player0)
        # A+B: 事件奖励基线 (每局重置)
        self._prev_mines = {}         # mine_id -> owner
        self._prev_levels = {}        # hero_id -> level
        self._last_battle_result = 0  # 0=无 1=red赢 2=red输 3=平局
        self._first_win_done = False  # 2026-08-25 方案a: 首胜标志每局重置
        self._visited = set()         # 探索奖励: 每局重置
        self._prev_nk2_value = 0.0    # Phase I.1: NK2 势函数前值
        if state is None:
            return
        for pi in range(state.player_count):
            p = state.players[pi]
            prev = self._prev_player0 if pi == 0 else self._prev_player1
            prev["gold"] = p.gold
            prev["wood"] = p.wood; prev["mercury"] = p.mercury
            prev["ore"] = p.ore; prev["sulfur"] = p.sulfur
            prev["crystal"] = p.crystal; prev["gems"] = p.gems
            prev["towns"] = p.town_count
            prev["heroes"] = p.hero_count
        # A+B: 记录初始矿归属与英雄等级 (只用于奖励计算, 不进 obs)
        for i in range(state.mine_count):
            m = state.mines[i]
            self._prev_mines[m.id] = m.owner
        for h in state.heroes:
            if h.id > 0:   # id<=0 为空槽位哨兵 (-1/0), 排除
                self._prev_levels[h.id] = h.level
        self._last_battle_result = state.battle_result
        # A+B: 探索预填出生区 — red(owner==0) 英雄出生位置为中心 3×3 (dx,dy∈[-1,1] 同层)
        # 解决出生区基线问题: 模型必须在出生区外探索才有奖励
        for h in state.heroes:
            if h.id > 0 and h.owner == 0:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        self._visited.add((h.pos_x + dx, h.pos_y + dy, h.pos_z))
        # Phase I.1: 计算初始 NK2 势函数值
        if self.use_nk2_shaping:
            self._prev_nk2_value = nk2_state_value(state)

    def _calc_reward(self, state: Optional[StrategicState]) -> float:
        """计算基于资源变化的奖励 (A+B: 矿/战斗/升级事件奖励; Phase I.1: NK2 势函数)"""
        if state is None:
            return 0.0

        # Phase I.1: NK2 势函数模式 — 用状态价值差分替代事件奖励
        if self.use_nk2_shaping:
            nk2_val = nk2_state_value(state)
            shaping_delta = (nk2_val - self._prev_nk2_value) * self.nk2_shaping_scale
            self._prev_nk2_value = nk2_val
            reward = self.reward_step_fixed + shaping_delta
            # I.1.3 诊断日志 (每步)
            if not hasattr(self, '_nk2_diag_step'):
                self._nk2_diag_step = 0
                print(f"[NK2_SHAPING] ON scale={self.nk2_shaping_scale} step_fixed={self.reward_step_fixed}", flush=True)
            self._nk2_diag_step += 1
            if self._nk2_diag_step <= 10 or self._nk2_diag_step % 50 == 0:
                print(f"[NK2] step={self._nk2_diag_step} nk2_val={nk2_val:.3f} delta={shaping_delta:.3f} reward={reward:.3f}", flush=True)
            # 仍需更新追踪变量 (mine/level/battle) 供其他模块使用
            for i in range(state.mine_count):
                m = state.mines[i]
                self._prev_mines[m.id] = m.owner
            for h in state.heroes:
                if h.id > 0:
                    self._prev_levels[h.id] = h.level
            # 2026-08-25 方案a: 战斗奖励 + 首胜加成 (NK2 模式下补战斗信号, 治"打赢被步数惩罚稀释")
            # 胜利/失败仍由 NK2 state_value 内的 ±50 处理, 这里补显式战斗奖励供长局可见
            if self._last_battle_result != 1 and state.battle_result == 1:
                reward += self.reward_battle_mult
                if not self._first_win_done:
                    reward += self.reward_first_win_bonus
                    self._first_win_done = True
            self._last_battle_result = state.battle_result
            if state.player_count >= 1:
                p0 = state.players[0]
                self._prev_player0 = {
                    "gold": p0.gold, "wood": p0.wood, "mercury": p0.mercury,
                    "ore": p0.ore, "sulfur": p0.sulfur, "crystal": p0.crystal, "gems": p0.gems,
                    "towns": p0.town_count, "heroes": p0.hero_count,
                }
            # H3 fix (2026-09-14): 终局显式 ±200 对齐非 NK2 分支 L1122-1126。
            # 旧设计"胜负只靠 NK2 state_value ±50 势差"在红灭瞬间失效: 终局快照
            # nk2_val 退化为有界值 (实测=10), shaping delta 仅 -26, 无法表达"无将无城
            # 判负"的强信号; 叠加本分支 clip 下限 -10 → 红败 r 被压成 -10, -200 信号丢失。
            # H3 终局通道 (-2 → game_over=2) 落地后, 在此补显式终局奖惩并把下限放宽到 -300。
            if self._game_over == 1:  # red wins
                reward += self.reward_win
            elif self._game_over == 2:  # blue wins
                reward -= self.reward_win
            # 探索奖励: 新格子访问 (保留, 让模型有动力移动)
            if self.reward_explore > 0:
                for h in state.heroes:
                    if h.id >= 0 and h.owner == 0:
                        for dx in (-1, 0, 1):
                            for dy in (-1, 0, 1):
                                pos = (h.pos_x + dx, h.pos_y + dy, h.pos_z)
                                if pos not in self._visited:
                                    self._visited.add(pos)
                                    reward += self.reward_explore
            return float(np.clip(reward, -300, 300))

        # === 原有事件奖励模式 (use_nk2_shaping=False 时走这里) ===
        reward = self.reward_step_fixed

        # 探索奖励: red 英雄访问新格子 (C8.5)
        if self.reward_explore > 0:
            for h in state.heroes:
                if h.id >= 0 and h.owner == 0:
                    pos = (h.pos_x, h.pos_y, h.pos_z)
                    if pos not in self._visited:
                        self._visited.add(pos)
                        reward += self.reward_explore

        # A+B: 矿奖励 — owner 从 !=0 变为 0 (red 新占矿) → +reward_mine_mult
        for i in range(state.mine_count):
            m = state.mines[i]
            prev_owner = self._prev_mines.get(m.id, m.owner)  # 新出现的矿不奖励
            if prev_owner != 0 and m.owner == 0:
                reward += self.reward_mine_mult
            self._prev_mines[m.id] = m.owner

        # A+B: 战斗奖励 — battle_result 从非1变为1 (red 打赢) → +reward_battle_mult
        # 2026-08-25 方案a: 首胜额外加成 (与 NK2 分支对称)
        if self._last_battle_result != 1 and state.battle_result == 1:
            reward += self.reward_battle_mult
            if not self._first_win_done:
                reward += self.reward_first_win_bonus
                self._first_win_done = True
        self._last_battle_result = state.battle_result

        # 本方 P0 (red) 的资源变化奖励
        if state.player_count >= 1:
            p0 = state.players[0]
            prev0 = self._prev_player0
            reward += (p0.gold - prev0["gold"]) * self.reward_gold_mult
            reward += (p0.wood - prev0["wood"]) * self.reward_gold_mult * 0.5
            reward += (p0.ore - prev0["ore"]) * self.reward_gold_mult * 0.5
            reward += (p0.mercury + p0.sulfur + p0.crystal + p0.gems -
                       prev0["mercury"] - prev0["sulfur"] - prev0["crystal"] - prev0["gems"]) * self.reward_gold_mult * 2
            reward += (p0.town_count - prev0["towns"]) * self.reward_town_mult
            reward += (p0.hero_count - prev0["heroes"]) * self.reward_hero_mult
            # C8.5 教训: exp per-step 奖励已删除 (交互漏洞: act=8 白拿 exp 奖励) — 改为升级事件奖励
            self._prev_player0 = {
                "gold": p0.gold, "wood": p0.wood, "mercury": p0.mercury,
                "ore": p0.ore, "sulfur": p0.sulfur, "crystal": p0.crystal, "gems": p0.gems,
                "towns": p0.town_count, "heroes": p0.hero_count,
            }

        # A+B: 升级奖励 — red 英雄 level 增加 → +reward_level_mult
        for h in state.heroes:
            if h.id > 0 and h.owner == 0:   # id<=0 为空槽位哨兵
                prev_lvl = self._prev_levels.get(h.id)
                if prev_lvl is not None and h.level > prev_lvl:
                    reward += self.reward_level_mult
                self._prev_levels[h.id] = h.level

        # 胜利奖励
        if self._game_over == 1:  # red wins
            reward += self.reward_win
        elif self._game_over == 2:  # blue wins
            reward -= self.reward_win  # punish for losing

        # 注意: clip 上下限对称放宽到 ±300 以容纳事件奖励 (战斗+100 / 胜利±200 同帧可达 300),
        # 2026-08-29 T04 修复: 原下限 -10 把失败 -200 剪成 -10, 输赢信号差仅 10 分 → 模型"输也无所谓"退化
        return float(np.clip(reward, -300, 300))

    def _check_done(self, state: Optional[StrategicState]):
        """检查是否终止"""
        terminated = False
        truncated = False

        if state is not None:
            # 游戏结束
            if state.game_over != 0:
                terminated = True

        # 回合上限
        if self._turn >= self.max_turns:
            truncated = True

        return terminated, truncated

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def random_action(self):
        """返回随机有效动作（用于测试）"""
        if self._terminated or self._truncated:
            return None
        return int(self.action_space.sample())

    def get_state_raw(self) -> Optional[StrategicState]:
        """返回原始 StrategicState 结构体（用于高级分析）"""
        return self._read_state()


# =============================================================================
# 注册环境
# =============================================================================

gym.register(
    id="VCMI-strategic-v1",
    entry_point="vcmi_gym.envs.v13.strategic_env:StrategicEnv",
    disable_env_checker=True,
)
