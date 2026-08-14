# =============================================================================
# strategic_env.py — VCMI 战略层 RL 环境 (gymnasium.Env)
#
# 基于冒险 API (adventure_wait/act) 实现红蓝自博弈训练。
# 观测：StrategicState 结构体 (ctypes 直读 libmlclient.so 的 g_strategic_state)
# 动作：Discrete(11) — 8方向移动 + 交互 + 下一英雄 + 结束回合
# 奖励：资源变化 + 领地扩张 + 英雄经验 + 胜利
# =============================================================================

import ctypes
import os
import threading
import time
from typing import Optional, Dict, Any

import gymnasium as gym
import numpy as np

# Set RTLD_GLOBAL for ALL subsequent dlopen calls
import sys as _sys
_ctypes = __import__("ctypes")
_sys.setdlopenflags(_sys.getdlopenflags() | _ctypes.RTLD_GLOBAL)

from ..util import log
# Preload libmlclient.so with RTLD_GLOBAL so dlsym finds our version first
import os as _os
_ctypes.CDLL(_os.environ.get("STRATEGIC_STATE_LIB", "/home/administrator/vcmi-native/rel/bin/libmlclient.so"), mode=_ctypes.RTLD_GLOBAL)
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

N_ACTIONS = 11

# 观测向量维度 (OBS schema v2: 8+96+184+112+225+2048+8+8 = 2689)
OBS_DIM = 2689

# StrategicState 最大实体数
MAX_PLAYERS = 8
MAX_HEROES = 8
MAX_TOWNS = 8

# OBS schema v2 态势感知段常量 (与 strategic_reader.py / C 头一致)
LOCAL_WIN = getattr(_sr, "LOCAL_WIN", 15)      # local_tiles 窗口边长
GLOBAL_GRID = getattr(_sr, "GLOBAL_GRID", 32)  # global_explored 网格边长
MAX_LEVELS = getattr(_sr, "MAX_LEVELS", 2)     # 地图层数


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
        # 默认 WSL2 路径 — 可通过环境变量覆盖
        lib_path = os.environ.get(
            "STRATEGIC_STATE_LIB",
            "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
        )

    if not os.path.exists(lib_path):
        # 尝试备用路径（直接从 WSL 内部）
        wsl_path = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
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
    """将 StrategicState ctypes 结构体展平为 1D numpy 观测向量 (OBS schema v2, 2689 维)

    布局 (索引从 0 开始):
      [0:8]      global          day,week,month,current_player,map_w,map_h,has_underground,player_count
      [8:104]    players         8 x 12
      [104:288]  heroes          8 x 23 (id..exp, army_count[7], in_battle)
      [288:400]  towns           8 x 14 (id,owner,pos xyz,buildings,garrison[7],gold_income)
      [400:625]  local window    15 x 15 = 225, state.local_tiles 行主序
      [625:2673] global explored 32 x 32 x 2 = 2048, 先 z=0 层再 z=1 层
      [2673:2681] active_hero    obs[2673]=state.active_hero, 其余保留 0
      [2681:2689] passable       永远在 OBS_DIM-8
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

    # --- Players (8 * 12 = 96) ---
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
        else:
            idx += 12  # 空槽位保持 0

    # --- Heroes (8 * 23 = 184) — 8 个英雄全装下, 无 264 维度截断 ---
    _HERO_FIELDS = 23
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
        else:
            idx += _HERO_FIELDS  # 空槽位保持 0

    # --- Towns (8 * 14 = 112) — 无城镇槽位填 0 ---
    _TOWN_FIELDS = 14
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
        else:
            idx += _TOWN_FIELDS  # 空槽位保持 0

    # --- Local window (15 * 15 = 225) — 行主序 (li 行, lj 列) ---
    # 注: ctypes 多维数组 (c_int8*15*15) 线性索引返回子数组, 需双重索引取标量
    for li in range(LOCAL_WIN):
        row = state.local_tiles[li]
        for lj in range(LOCAL_WIN):
            obs[idx] = row[lj]
            idx += 1

    # --- Global explored (32 * 32 * 2 = 2048) — 先 z=0 层 1024 维, 再 z=1 层 ---
    for z in range(MAX_LEVELS):
        layer = state.global_explored[z]
        for gy in range(GLOBAL_GRID):
            row = layer[gy]
            for gx in range(GLOBAL_GRID):
                obs[idx] = row[gx]
                idx += 1

    # --- Active hero (8) — obs[2673] 为 active_hero (int32, -1 或索引), [2674:2681] 保留 0 ---
    obs[OBS_DIM - 16] = state.active_hero

    # --- Passability (8) — 永远在 OBS_DIM-8 ---
    pidx = OBS_DIM - 8
    for di in range(8):
        obs[pidx + di] = state.passable[di]

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
        reward_step_fixed: float = -1.5,  # 2026-08-02: -0.1 太弱致 END_TURN 刷底无成本 (用户原则 -1.0~-2.0 压制不动)
        reward_explore: float = 0.0,   # 探索奖励: 访问新格子 (C8.5)
        # A+B: 事件奖励 (占矿/打赢战斗/英雄升级)
        reward_mine_mult: float = 10.0,    # 占矿 (owner !=0 → 0)
        reward_battle_mult: float = 100.0, # 打赢战斗 (battle_result 0/2/3 → 1)
        reward_level_mult: float = 10.0,   # 英雄升级
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
        self.reward_step_fixed = reward_step_fixed
        self.reward_explore = reward_explore
        # A+B: 事件奖励系数
        self.reward_mine_mult = reward_mine_mult
        self.reward_battle_mult = reward_battle_mult
        self.reward_level_mult = reward_level_mult
        self._visited = set()  # 已访问格子 (探索奖励)

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
            randomArmies=False,
            randomArmyValueMin=500,
            randomArmyValueMax=1000,
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
            return obs, info

        # 读取初始状态（VCMI 已在 process_turn 阻塞，状态已更新）
        state = self._read_state()
        obs = self._build_obs(state)

        # 初始化奖励跟踪基线
        self._init_baselines(state)

        info = {
            "day": state.day if state else 1,
            "current_player": state.current_player if state else 0,
            "turn": self._turn,
        }
        return obs, info

    @tracelog
    def step(self, action: int):
        """
        执行动作，返回 (obs, reward, terminated, truncated, info)

        动作 0-7: 移动方向
        动作 8:    交互 (拾取/对话/攻击)
        动作 9:    切换到下一英雄
        动作 10:   结束回合

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

        # 计算奖励
        reward = self._calc_reward(state)
        # 2026-08-02: 连续 END_TURN 惩罚 — 第 3 次起每次固定 -5 (C8.5 塌缩刷底无成本根因; 固定值避免 n 递增爆炸 -32889)
        if self._consecutive_endturn >= 3:
            reward -= 5.0

        # 检测终止
        self._terminated, self._truncated = self._check_done(state)

        info = {
            "day": state.day if state else 1,
            "current_player": state.current_player if state else 0,
            "game_over": self._game_over,
            "turn": self._turn,
        }
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
            timeout = min(self._vcmi_timeout, 120)
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
            lib_name = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
            try:
                # 先用 CDLL 加载（如果尚未加载，RTLD_NOLOAD 方式不可靠）
                lib_path = self.libml_path or os.environ.get("STRATEGIC_STATE_LIB",
                    "/home/administrator/vcmi-native/rel/bin/libmlclient.so")
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
        self._visited = set()         # 探索奖励: 每局重置
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

    def _calc_reward(self, state: Optional[StrategicState]) -> float:
        """计算基于资源变化的奖励 (A+B: 矿/战斗/升级事件奖励)"""
        if state is None:
            return 0.0

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
        if self._last_battle_result != 1 and state.battle_result == 1:
            reward += self.reward_battle_mult
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

        # 注意: clip 上限放宽到 300 以容纳事件奖励 (战斗+100 / 胜利+200 同帧可达 300),
        # 原 clip(-10,10) 会把 +100 战斗奖励压到 +10, 使事件奖励失效
        return float(np.clip(reward, -10, 300))

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
