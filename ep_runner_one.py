import sys, os, json, argparse, random, zipfile
from collections import deque
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
import torch, torch.nn as nn
import numpy as np  # 2026-08-19 第5轮: MOVE_TO 展开用 np.asarray — 第4轮 24 零出现掩盖了缺失 (强制引导后必炸)
from torch.distributions import Categorical
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

# --- BFS 寻路 (Phase I.2): 用 local_tiles 通行性格子绕障碍 ---
# local_tiles[0] 15×15 在 obs[480:705], 英雄在 (7,7)
# 0=未知, 1=可走, 2=障碍
_DIRS = [(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]  # 0-7 对应方向
_DIR_TO_ACT = [0,1,2,3,4,5,6,7]  # 方向 → 动作码

def bfs_path(obs, tx, ty):
    """在 local_tiles 通行性格子上 BFS, 返回从英雄到 (tx,ty) 的第一步方向, 或 None。
    tx,ty 是绝对地图坐标。英雄在 obs[3203] 对应的 hero slot。
    返回: 方向动作码 (0-7), 或 None (不可达/超出视野)"""
    ah = int(obs[3203]) if obs[3203] >= 0 else 0
    base = 128 + ah * 26
    hx, hy = int(obs[base+2]), int(obs[base+3])
    # 目标相对坐标
    dx, dy = tx - hx, ty - hy
    if abs(dx) > 7 or abs(dy) > 7:
        return None  # 超出 15×15 视野
    if dx == 0 and dy == 0:
        return None  # 已到达
    # 读取 15×15 通行性 (channel 0, obs[480:480+225])
    grid = np.zeros((15, 15), dtype=np.int8)
    for y in range(15):
        for x in range(15):
            grid[y][x] = int(obs[480 + y * 15 + x])
    # BFS 从 (7,7) 到 (7+dx, 7+dy)
    start = (7, 7)
    goal = (7 + dx, 7 + dy)
    if goal[0] < 0 or goal[0] >= 15 or goal[1] < 0 or goal[1] >= 15:
        return None
    if grid[goal[1]][goal[0]] == 2:
        return None  # 目标不可走
    visited = set()
    visited.add(start)
    queue = deque([(start, [])])
    while queue:
        (cx, cy), path = queue.popleft()
        for d, (ddx, ddy) in enumerate(_DIRS):
            nx, ny = cx + ddx, cy + ddy
            if 0 <= nx < 15 and 0 <= ny < 15 and (nx, ny) not in visited:
                if grid[ny][nx] == 1:  # 可走
                    new_path = path + [d]
                    if (nx, ny) == goal:
                        return _DIR_TO_ACT[new_path[0]]  # 返回第一步方向
                    visited.add((nx, ny))
                    queue.append(((nx, ny), new_path))
    return None  # 不可达

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(3464,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        # CNN branch for terrain grid (4,21,21) -> 128
        self.cnn = nn.Sequential(
            nn.Conv2d(4, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 21->10
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 10->5
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),                    # 5->5
            nn.Flatten(),                                                   # 64*5*5=1600
            nn.Linear(1600, 128), nn.ReLU()
        )
        # Merge: obs(128) + cnn(128) = 256 -> 128
        self.merge = nn.Sequential(nn.Linear(256, 128), nn.ReLU())
        self.actor, self.critic = nn.Linear(128,25), nn.Linear(128,1)
    def forward(self, x, terrain=None):
        h_obs = self.fc(x)
        if terrain is not None:
            h_cnn = self.cnn(terrain)
            h = self.merge(torch.cat([h_obs, h_cnn], dim=-1))
        else:
            h = self.merge(torch.cat([h_obs, torch.zeros_like(h_obs)], dim=-1))
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

parser = argparse.ArgumentParser()
parser.add_argument("max_turns", nargs="?", type=int, default=10)
parser.add_argument("outfile", nargs="?", type=str, default="/tmp/traj_one.json")
parser.add_argument("mapname", nargs="?", type=str, default="Key to Victory.h3m")
parser.add_argument("--model", type=str, default=None,
                    help="Path to red model checkpoint (uses model policy instead of random)")
parser.add_argument("--blue_model", type=str, default=None,
                    help="Path to blue model checkpoint")
parser.add_argument("--blue_ai", type=str, default=None,
                    help="AI type for blue player (MMAI_USER, StupidAI, etc.)")
parser.add_argument("--blue_adventure_ai", type=str, default="Nullkiller2",
                    help="冒险AI for blue player (C8.5: Nullkiller2 真对手)")
parser.add_argument("--move_to_test", action="store_true", help="强制所有动作=24 (MOVE_TO 测试)")
parser.add_argument("--move_to_bias", type=float, default=0.0, help="MOVE_TO(24) logits 探索偏置 (训练早期引导)")
parser.add_argument("--move_to_force", type=int, default=0, help="MOVE_TO(24) 采样强制: 每局前 N 步强制动作 24 (第5轮: 引导模型发现目标导向动作)")
parser.add_argument("--economy_force", type=int, default=0,
                    help="经济动作采样强制 (Level 3): 每局前 N 步强制 16-21 轮换 (RECRUIT_1/2/3, BUILD_1/2/3) — 模型从没见过这些码, 需采样强制引导")
parser.add_argument("--cycle_detect", type=int, default=0, help="状态级循环检测: 8 步窗口内同一 (hero,pos) 出现 >=N 次 → -3 惩罚 + 强制随机方向 (0=关闭)")
parser.add_argument("--act_loop_penalty", type=float, default=0.0,
                    help="动作级循环惩罚 (第7轮): 连续 N 步重复 / 固定两两交替 → 负 reward (0=关闭)")
parser.add_argument("--act_loop_repeat", type=int, default=4,
                    help="动作级循环: 连续重复 N 步判死循环")
parser.add_argument("--act_loop_alt", type=int, default=8,
                    help="动作级循环: 两两交替窗口步数 (偶数, 8 = [a,b]x4)")
parser.add_argument("--act_loop_p3", type=int, default=9,
                    help="动作级循环: 三阶周期窗口步数 (9 = [a,b,c]x3)")
parser.add_argument("--reward_explore", type=float, default=0.0,
                    help="探索奖励: 访问新格子 +N (C8.5)")
parser.add_argument("--use_nk2_shaping", action="store_true",
                    help="Phase I.1: 用 NK2 势函数差分替代事件奖励")
parser.add_argument("--nk2_shaping_scale", type=float, default=1.0,
                    help="NK2 势函数差分缩放")
parser.add_argument("--guard_grad_scale_by_map", action="store_true",
                    help="P3 (BND-20260828-01 解封): 守卫接近梯度按图幅缩放 — rate=0.5*(宽/20), 30x30→0.75, 36x36→0.9; 默认关 (20x20 行为不变, 不污染在跑 A/B)")
parser.add_argument("--random_armies", action="store_true",
                    help="随机军队 (用randomArmyValue范围)")
parser.add_argument("--random_army_min", type=int, default=500,
                    help="随机军队最低价值 (默认500)")
parser.add_argument("--random_army_max", type=int, default=1000,
                    help="随机军队最高价值 (默认1000)")
parser.add_argument("--guard_done_steps", type=int, default=0,
                    help="守卫击杀自动终局 (2026-08-29): +100 守卫胜利后 N 步内未获取新目标 → 提前结束 episode (0=关闭)。治杀守卫后英雄存活长期振荡烧分, final r 跌破 80 晋级线")
parser.add_argument("--objective_reward", type=float, default=0.0,
                    help="T04 目标引导 (2026-08-29): 首占矿/首进城镇各 +N 一次性事件奖励 (0=关闭)。T04 无守卫缺目标驱动源, 复用守卫 +100 同款模式")
args = parser.parse_args()

# 2026-08-25: 守卫目标 — C++ target_list 无守卫 (重编环境崩无法部署), Python 从 vmap 读守卫位置补进 MOVE_TO 目标池
# 守卫在矿 8 邻, 从英雄视角常比矿更近 → 先走向守卫 → 触发战斗 (T03 课程目标)
_GUARD_CACHE = {}
def get_guards(mapname):
    if mapname not in _GUARD_CACHE:
        try:
            p = f"/mnt/d/Bigdata/hero3_fresh/maps/training/{mapname}"
            with zipfile.ZipFile(p) as z:
                objs = json.loads(z.read("objects.json"))
            _GUARD_CACHE[mapname] = [(int(o["x"]), int(o["y"]), int(o.get("l", 0)))
                                     for k, o in objs.items() if k.startswith("monster_")]
        except Exception as e:
            _GUARD_CACHE[mapname] = []
    return _GUARD_CACHE[mapname]

_MAP_SIZE_CACHE = {}
_OBJ_CACHE = {}
def get_objectives(mapname):
    """T04 目标点 (2026-08-29 引导奖励用): 返回 (mines, towns) 坐标列表, 从 vmap objects.json 读取"""
    if mapname not in _OBJ_CACHE:
        try:
            p = f"/mnt/d/Bigdata/hero3_fresh/maps/training/{mapname}"
            with zipfile.ZipFile(p) as z:
                objs = json.loads(z.read("objects.json"))
            mines = [(int(o["x"]), int(o["y"])) for k, o in objs.items() if k.startswith("mine_")]
            towns = [(int(o["x"]), int(o["y"])) for k, o in objs.items() if k.startswith("town_")]
            _OBJ_CACHE[mapname] = (mines, towns)
        except Exception:
            _OBJ_CACHE[mapname] = ([], [])
    return _OBJ_CACHE[mapname]

def get_map_width(mapname):
    """P3: 从 vmap header.json 读地图宽度 (mapLevels.surface.width); 失败回退文件名 XnXm 解析, 再失败 0"""
    if mapname not in _MAP_SIZE_CACHE:
        w = 0
        try:
            p = f"/mnt/d/Bigdata/hero3_fresh/maps/training/{mapname}"
            with zipfile.ZipFile(p) as z:
                h = json.loads(z.read("header.json"))
            w = int(h["mapLevels"]["surface"]["width"])
        except Exception:
            import re as _re
            m = _re.search(r"(\d+)[Xx](\d+)", mapname)
            if m: w = int(m.group(1))
        _MAP_SIZE_CACHE[mapname] = w
    return _MAP_SIZE_CACHE[mapname]

# 2026-08-28 Level 3: 资源点 (矿/资源堆) 缓存 — 经济闭环奖励检测：访问资源点→50步内招兵=+15
# 从 vmap objects.json 读 mine_* (金矿等) 和 resource_* (木/矿堆)，记录 (x,y)
_RESOURCE_CACHE = {}
def get_resource_points(mapname):
    if mapname not in _RESOURCE_CACHE:
        try:
            p = f"/mnt/d/Bigdata/hero3_fresh/maps/training/{mapname}"
            with zipfile.ZipFile(p) as z:
                objs = json.loads(z.read("objects.json"))
            pts = []
            for k, o in objs.items():
                if k.startswith("mine_") or k.startswith("resource_"):
                    try:
                        pts.append((int(o["x"]), int(o["y"])))
                    except:
                        pass
            _RESOURCE_CACHE[mapname] = pts
        except Exception as e:
            _RESOURCE_CACHE[mapname] = []
    return _RESOURCE_CACHE[mapname]

# Load red model if provided
red_model = None
if args.model and os.path.exists(args.model):
    red_model = Net()
    red_model.eval()
    try:
        sd = torch.load(args.model, map_location="cpu", weights_only=True)
        red_model.load_state_dict(sd, strict=False)
    except:
        try:
            sd = torch.load(args.model, map_location="cpu", weights_only=False)
            if "model" in sd:
                red_model.load_state_dict(sd["model"], strict=False)
            else:
                red_model.load_state_dict(sd, strict=False)
        except:
            red_model = None

traj = {"obs": [], "act": [], "rew": [], "nobs": [], "done": [], "terrain_grid": [], "steps": 0, "total_rew": 0.0}
try:
    env = StrategicEnv(
        mapname=args.mapname, max_turns=args.max_turns,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR", red="StupidAI", blue=args.blue_ai or "StupidAI",
        random_heroes=0, boot_timeout=120, vcmi_timeout=900,  # 2026-08-25: random_heroes 1→0 (随机出生点 → 部分局离矿 40+ 格, 课程战斗目标被稀释)
        red_model_path=args.model or "",
        blue_model_path=args.blue_model or "",
        blue_adventure_ai=args.blue_adventure_ai,
        reward_explore=args.reward_explore,
        use_nk2_shaping=args.use_nk2_shaping,
        nk2_shaping_scale=args.nk2_shaping_scale,
        random_armies=args.random_armies,
        random_army_min=args.random_army_min,
        random_army_max=args.random_army_max,
    )
    obs, _info = env.reset(); tg = _info.get("terrain_grid"); traj["terrain_grid"].append(tg.tolist() if tg is not None and hasattr(tg, "tolist") else [])
    interact_streak = 0  # ML fix (2026-08-17): INTERACT 冷却
    endturn_streak = 0  # 2026-08-19: END_TURN 冷却 — 连续 3 次屏蔽, 防跳过游戏刷步
    zombie_streak = 0  # 2026-08-28: 全堵(英雄死亡)连续计数, >=2 确认死亡立即终局
    move_target = None  # MOVE_TO 粘滞目标 (tx,ty,tz) — 防目标漂移来回走
    move_guard_target = False  # 2026-08-25: 目标是否为守卫 (守卫格 passable=0, 跳过 passable 检查)
    move_stall = 0
    move_stall_prev = 10**9
    prev_passable = {}   # 2026-08-26: 守卫格 passable 基线 (守卫清除检测)
    guard_first_win = False  # 2026-08-26: 首胜 (守卫清除) 已发
    guard_done_countdown = None  # 2026-08-29: 守卫胜利后自动终局倒计时 (None=未触发/关闭; 新目标重置)
    prev_guard_d = None  # 2026-08-27 方案A: 守卫接近梯度基线 (最近守卫曼哈顿距离)
    # P3 (BND-20260828-01 解封): 接近梯度 rate, 默认 0.5; --guard_grad_scale_by_map 时按图幅放大
    guard_grad_scale = 0.5
    if args.guard_grad_scale_by_map:
        _w = get_map_width(args.mapname)
        if _w: guard_grad_scale = 0.5 * max(1.0, _w / 20.0)  # 20x20→0.5, 30x30→0.75, 36x36→0.9
    # === 2026-08-28 Level 3: 经济成型奖励 4 条 跟踪变量 ===
    # 优先级1: 首 RECRUIT (16,17,18) 每档 +5, 每档一局仅一次
    econ_recruit_first = {16: False, 17: False, 18: False}
    # 优先级2: 首 BUILD_2 (动作20=兵种建筑) +8, 一局一次
    econ_build2_done = False
    # 优先级3: 兵力总 power 差分 (招兵/战斗损耗) → 增量×0.001
    #   heroes slot: 每英雄 26 字段, field 10-19 = 5 slots × (creature_id, count)
    #   weight 近似 VCMI AI value: slot0 (1级兵)×10, slot1×40, slot2×120, slot3×350, slot4×900
    econ_prev_army_power = None
    # 优先级4: 闭环「访问资源点 (首次踩矿/资源堆格记步) → 50步内招兵」+15, 一局一次
    econ_resource_step = None  # 最近访问资源点的步数 (None=没访问过)
    econ_closure_done = False
    # T04 目标引导 (2026-08-29): 首占矿/首进城镇 各 +N 一局一次
    mine_taken = False
    town_visited = False
    town_blocked = False     # 城镇贪心卡死 → 本局禁用城优先
    move_town_target = False # 当前粘滞目标是否为城镇 (卡死判定用)
    # (动作合法性由 s2b 掩码保证 — 非法 16-21 根本不会被采样, 所以"尝试动作"≈"动作成功")
    # (被拒交互后 obs 不变 → 一直选 8 → 死循环 → 触发 server bug 崩溃)。连续 8 上限 2 次。
    act_hist = []  # 动作级循环检测: 最近动作序列 (第7轮)
    for _ in range(args.max_turns):
        cycle_penalty = 0.0
        force_dir = None
        zombie = False  # 2026-08-28: 英雄死亡(全堵)检测 → 立即终局, 防僵尸段
        if red_model is not None:
            with torch.no_grad():
                obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
                # 地形栅格 CNN 输入 (2026-08-24 修复): 采样端之前漏传 terrain → CNN 全零, 模型决策看不到水/岩
                # 训练端 model(obs_t, terrain_t) 已传真实地形, 两端必须一致 (行为=学习)
                tg = traj["terrain_grid"][-1] if traj["terrain_grid"] else None
                terrain_t = (torch.tensor(np.array(tg, dtype=np.float32), dtype=torch.float32).unsqueeze(0)
                             if tg is not None and len(tg) else None)
                pi, _ = red_model(obs_t, terrain_t)
                # Passability mask: OBS v3 obs[3211:3219] = 8方向可通行性
                passable = torch.tensor(obs[3211:3219], dtype=torch.bool)
                logits = pi.logits[0].clone()
                if passable.any():
                    logits[:8][~passable] = float('-inf')  # 非法方向概率归零
                    # INTERACT 冷却: 连续动作 8 >= 2 次时屏蔽
                    if interact_streak >= 2:
                        logits[8] = float('-inf')
                    # 2026-08-24: 屏蔽内政动作 (RECRUIT_1/2/3=16-18, BUILD_1/2/3=19-21, GARRISON=22, RECRUIT_HERO=23)
                    # 目标: 先学会地图探索, 内政关闭直到能把官方地图跑通
                    # 2026-08-27: 屏蔽无操作动作 — 训练构建真源 (vcmi-native-build) only executes 0-7/24; 8/9/11-15 无执行分支 (纯浪费步)
                    # ========== 永久屏蔽段 (Level 0-5 不变) ==========
                    # 8=INTERACT / 9=NEXT_HERO / 11-15=SPLIT/MERGE: vcmi-native-build 真源无 switch 执行分支 → 纯NOOP刷步
                    logits[8] = float('-inf')
                    logits[9] = float('-inf')
                    logits[11:16] = float('-inf')
                    # ========== 内政动作 (16-23): Level 3 (T04) 起按需开启 ==========
                    # 22=GARRISON (需双目标) / 23=RECRUIT_HERO (需多英雄槽): 永久关, Level 4 多英雄再评估
                    logits[22:24] = float('-inf')
                    if not args.mapname.startswith("T04"):
                        # 非 T04 地图 (当前 Level 2 = T03×2): 16-21 全屏蔽, 行为 100% 等价旧代码
                        logits[16:22] = float('-inf')
                        # (模型从没见过这些码 (BC 无样本) → logits 极负, 需 --economy_force 采样强制引导)
                    else:
                        # === T04 (有城镇): 16-18 RECRUIT + 19-21 BUILD 开, 但需两道硬门槛 ===
                        # 门槛1: 位域合法性 (VCMI 引擎直接暴露的解锁状态)
                        #   recruit_mask 256 bits @ obs[640:672] (32 bytes): bit i = 兵种 i 可招募
                        #   build_mask 256 bits @ obs[672:704] (32 bytes):   bit i = 建筑 i 可建造
                        #   我们只关心各 3 档 tier: 0/1/2 对 RECRUIT act16/17/18, BUILD act19/20/21
                        def _bit_set(obs_bytes, base, bit_idx):
                            try:
                                byte_idx = base + (bit_idx >> 3)
                                return (int(obs_bytes[byte_idx]) >> (bit_idx & 7)) & 1 == 1
                            except:
                                return False  # OOB 保险: 视为非法不开放
                        recruit_legal = {tier: _bit_set(obs, 640, tier) for tier in range(3)}
                        build_legal   = {tier: _bit_set(obs, 672, tier) for tier in range(3)}
                        # 门槛2: 玩家资源阈值 (obs[304:311] = [gold, wood, ore, gems, crystal, sulfur, mercury])
                        #   Tier 对应成本: 1级兵≈50金1木; 2级兵≈150金5木; 3级兵≈300金10矿
                        try:
                            res_ok = {
                                'gold_t0': int(obs[304]) >= 50,
                                'gold_t1': int(obs[304]) >= 150,
                                'gold_t2': int(obs[304]) >= 300,
                                'wood_t0': int(obs[305]) >= 1,
                                'wood_t1': int(obs[305]) >= 5,
                                'ore_t2':  int(obs[306]) >= 10,
                            }
                        except:
                            res_ok = {k: False for k in
                                ['gold_t0','gold_t1','gold_t2','wood_t0','wood_t1','ore_t2']}
                        # --- RECRUIT_1/2/3 = act16/17/18: 位域合法 + 对应 tier 资源够才开 ---
                        for tier, act in enumerate([16, 17, 18]):
                            tier_ok = (
                                recruit_legal[tier]
                                and res_ok[f'gold_t{tier}']
                                and (res_ok[f'wood_t{tier}'] if tier <= 1 else res_ok['ore_t2'])
                            )
                            if not tier_ok:
                                logits[act] = float('-inf')
                        # --- BUILD_1/2/3 = act19/20/21: 位域合法才开 (资源消耗由引擎内部再校验, 此处按解锁位做前置粗筛) ---
                        for tier, act in enumerate([19, 20, 21]):
                            if not build_legal[tier]:
                                logits[act] = float('-inf')
                        # 注: 非法 16-21 置 -inf 后, 采样必不会命中 → s2a 的 [ECON] 奖励不会假阳性
                        # 注: BC 无这些动作样本 → 即便合法, logits 也极负 → 需 --economy_force 前50步硬采样引导
                    # END_TURN 冷却: 连续 3 次 → 屏蔽 (防跳过游戏刷步, C8.5 老问题复发)
                    if endturn_streak >= 3:
                        logits[10] = float('-inf')
                    # MOVE_TO 探索偏置 (训练早期引导模型输出 24)
                    if args.move_to_bias > 0:
                        logits[24] += args.move_to_bias
                    # === 状态级循环检测 (2026-08-19 第5轮): 8 步窗口同一 (hero,pos) >=N 次 → 惩罚+强制随机方向 ===
                    # 治 [8,8,6,2]/[8,3] 类动作循环 — 横跳惩罚(位置级)只能抓 3/7 往返, 抓不到动作级循环
                    if args.cycle_detect > 0 and len(traj["obs"]) >= 8:
                        ah = int(obs[3203]) if obs[3203] >= 0 else 0
                        base = 128 + ah * 26
                        cur_sign = (ah, int(obs[base+2]), int(obs[base+3]))
                        hist = []
                        for o in traj["obs"][-8:]:
                            a2 = int(o[3203]) if o[3203] >= 0 else 0
                            b2 = 128 + a2 * 26
                            hist.append((a2, int(o[b2+2]), int(o[b2+3])))
                        if hist.count(cur_sign) >= args.cycle_detect:
                            cycle_penalty = -3.0
                            dirs = [d for d in range(8) if bool(passable[d])]
                            if dirs:
                                force_dir = random.choice(dirs)
                    if force_dir is not None:
                        a = force_dir
                    else:
                        a = Categorical(logits=logits).sample().item()
                else:
                    zombie = True  # 2026-08-28: 8方向全堵 = 英雄已死(无活动英雄) → 僵尸段
                    a = 10  # 全堵→END_TURN
        else:
            a = int(env.action_space.sample())
        # MOVE_TO 采样强制 (2026-08-19 第5轮): 每局前 N 步强制动作 24 — 第4轮 bias(+2.0) 对从未见过的码无效 (24 零出现)
        if args.move_to_force > 0 and traj["steps"] < args.move_to_force and red_model is not None:
            a = 24
        # 经济动作采样强制 (2026-08-24 Level 3): 每局前 N 步强制 16-21 轮换 (RECRUIT/BUILD 引导)
        # 模型从未见过这些码 → logits 极负 → bias 无效, 采样强制 (move_to_force 同款教训)
        if args.economy_force > 0 and traj["steps"] < args.economy_force and red_model is not None:
            econ_acts = [16, 17, 18, 19, 20, 21]  # RECRUIT_1/2/3, BUILD_1/2/3 轮换
            a = econ_acts[traj["steps"] % len(econ_acts)]
        # MOVE_TO (24): 朝 target_list 目标走一格 (目标导向采集, 2026-08-19)
        # 粘滞: 上次目标未到达则继续用 (防漂移来回走); target_list obs[3251:3315] 8x8: type,idx,x,y,z,dist,power,flags
        if a == 24:
            ah = int(obs[3203]) if obs[3203] >= 0 else 0
            base = 128 + ah * 26
            hx, hy, hz = int(obs[base+2]), int(obs[base+3]), int(obs[base+4])
            tx = ty = tz = None
            next_dir_idx = -1  # I.2: 默认无 next_dir
            if move_target is not None:
                tx, ty, tz = move_target
                if tx is None or (abs(tx - hx) + abs(ty - hy) == 0):
                    if tx is not None:
                        move_target = None  # 已到达
                        move_guard_target = False
                        move_town_target = False
                else:
                    # 粘滞: 查找 target_list 匹配索引获取 next_dir
                    tl_tmp = np.asarray(obs[3251:3315], dtype=np.float32).reshape(8, 8)
                    for _i, _tt in enumerate(tl_tmp):
                        if int(_tt[2]) == tx and int(_tt[3]) == ty:
                            next_dir_idx = _i
                            break
                    # 守卫目标不在 target_list (C++ 未填), 恢复守卫标记
                    move_guard_target = any((tx == g[0] and ty == g[1]) for g in get_guards(args.mapname))
                    # 城镇目标 (Python 注入, C++ 不填) — 恢复标记 (卡死禁用判定用)
                    move_town_target = any((tx == _tw[0] and ty == _tw[1])
                                           for _tw in get_objectives(args.mapname)[1])
            if tx is None:
                tl = np.asarray(obs[3251:3315], dtype=np.float32).reshape(8, 8)
                best = None
                next_dir_idx = -1
                for i, tt in enumerate(tl):
                    if tt[5] > 0 and (best is None or tt[5] < best[5]):
                        best = tt
                        next_dir_idx = i
                # 2026-08-25: 守卫恒优先 — 守矿机制: 先占矿守卫消失, 战斗永不触发 → 守卫在 15 格内一律先打守卫
                # 一步可达 (8 邻) 的守卫优先 (直接从英雄格进守卫, 避免经过矿/资源)
                guard_best = None
                for (gx, gy, gz) in get_guards(args.mapname):
                    if gz != hz:
                        continue
                    gd = abs(gx - hx) + abs(gy - hy)
                    adj = (gd <= 2 and abs(gx - hx) <= 1 and abs(gy - hy) <= 1)
                    if 0 < gd < 15 and (
                        guard_best is None or
                        (adj and not guard_best[3]) or
                        (adj == guard_best[3] and gd < guard_best[0])
                    ):
                        guard_best = (gd, gx, gy, adj)
                # 2026-08-29 T04 目标优先层: obj_best = 矿 (target_list type=1) —
                # 占领后 (mine_taken) 排除防粘死。
                # 2026-08-29 II.3 调优: 城镇注入降级移除 — RECRUIT/BUILD 为玩家级远程操作无需到城,
                # 城镇贪心远距必卡死 (每次烧 6 步探测 + [TOWN_BLOCKED] 常态触发), [TOWN] +30 降级为路过事件 (下方检测保留)
                obj_best = None
                if args.objective_reward > 0 and not mine_taken:
                    for i, tt in enumerate(tl):
                        if int(tt[0]) == 1 and int(tt[5]) > 0 and (
                            obj_best is None or int(tt[5]) < obj_best[0]
                        ):
                            obj_best = (int(tt[5]), int(tt[2]), int(tt[3]), int(tt[4]), i)
                if guard_best is not None:
                    tx, ty, tz = guard_best[1], guard_best[2], hz
                    next_dir_idx = -1  # 无 C++ next_dir → 走 BFS/贪心
                    move_target = (tx, ty, tz)
                    move_stall = 0
                    move_guard_target = True  # 2026-08-25: 守卫格 passable=0 (blocked), 需跳过 passable 检查
                    move_town_target = False
                    if guard_done_countdown is not None:
                        guard_done_countdown = args.guard_done_steps  # 新目标 (余守卫) → 重置倒计时
                elif obj_best is not None:
                    # 2026-08-29 T04 目标优先: 矿/城镇恒优先于最近资源堆 —
                    # 资源堆 dist 近恒压过矿 → 模型被资源堆吸住, 远矿/城永远轮不到 (r=-80~-110 根因)。
                    # 矿有 C++ next_dir 支撑远距可达; 城镇贪心卡死由 move_stall 放弃处 town_blocked 兜底
                    tx, ty, tz = obj_best[1], obj_best[2], obj_best[3]
                    next_dir_idx = obj_best[4]  # 矿= target_list slot (C++ next_dir); 城镇= -1 (Python BFS/贪心)
                    move_target = (tx, ty, tz)
                    move_stall = 0
                    move_guard_target = False
                    move_town_target = (next_dir_idx == -1)
                    if guard_done_countdown is not None:
                        guard_done_countdown = args.guard_done_steps
                elif best is not None:
                    tx, ty, tz = int(best[2]), int(best[3]), int(best[4])
                    move_target = (tx, ty, tz)
                    move_stall = 0
                    move_guard_target = False
                    move_town_target = False
                    if guard_done_countdown is not None:
                        guard_done_countdown = args.guard_done_steps  # 新目标 (矿/资源) → 重置倒计时
                else:
                    move_target = None
                    move_guard_target = False
                    move_town_target = False
            if tx is not None:
                # Phase I.2: 优先用 C++ 全图 BFS (obs[3330:3338] = next_dir[8])
                nd = int(obs[3330 + next_dir_idx]) if next_dir_idx >= 0 else -1
                if nd >= 0:
                    a = nd
                else:
                    # 回退: 旧 15×15 BFS (守卫目标跳过 — BFS 按可通行性会绕开守卫格)
                    if not move_guard_target:
                        bfs_dir = bfs_path(obs, tx, ty)
                        if bfs_dir is not None:
                            a = bfs_dir
                    if a == 24 or (not move_guard_target and (a < 0 or a > 7)):
                        # BFS 失败 (目标超出视野/不可达), 回退贪心方向
                        dx, dy = tx - hx, ty - hy
                        cand = []
                        if abs(dx) > abs(dy):
                            cand = [2 if dx > 0 else 6]
                            if dy > 0: cand.append(3 if dx > 0 else 5)
                            elif dy < 0: cand.append(1 if dx > 0 else 7)
                        elif abs(dy) > abs(dx):
                            cand = [4 if dy > 0 else 0]
                            if dx > 0: cand.append(3 if dy > 0 else 1)
                            elif dx < 0: cand.append(5 if dy > 0 else 7)
                        else:
                            if dx > 0 and dy > 0: cand = [3, 2, 4]
                            elif dx > 0: cand = [1, 2, 0]
                            elif dy > 0: cand = [5, 4, 6]
                            else: cand = [7, 0, 6]
                        pas = [int(x) for x in obs[3211:3219]]
                        # 守卫目标: 优先走"下一格即守卫"方向 (直接进守卫格触发战斗, 避免经过矿/资源)
                        if move_guard_target:
                            guard_set = {(g[0], g[1]) for g in get_guards(args.mapname)}
                            for d in cand:
                                nx2, ny2 = hx + [0,1,1,1,0,-1,-1,-1][d], hy + [-1,-1,0,1,1,1,0,-1][d]
                                if (nx2, ny2) in guard_set:
                                    a = d
                                    break
                            if a == 24:
                                for d in cand:
                                    if pas[d] or move_guard_target:  # 守卫格 passable=0 (blocked) 但可攻击进入 (2026-08-25)
                                        a = d
                                        break
                        else:
                            for d in cand:
                                if pas[d]:
                                    a = d
                                    break
                # 卡住检测: 连续 6 步距离不减小 → 放弃换目标 (被堵/绕路)
                cur_dist = abs(tx - hx) + abs(ty - hy)
                if cur_dist >= move_stall_prev:
                    move_stall += 1
                else:
                    move_stall = 0
                move_stall_prev = cur_dist
                if move_stall >= 6:
                    if move_town_target and args.objective_reward > 0 and not town_blocked:
                        town_blocked = True  # 城镇贪心卡死 → 本局禁用城优先, 防无限卡城循环
                        print(f"[TOWN_BLOCKED] town unreachable via greedy, disable town priority at step {traj['steps']}", flush=True)
                    move_target = None
                    move_stall = 0
            else:
                zombie = True
                a = 10  # 无目标可采 → END_TURN
        else:
            move_target = None  # 模型输出其他动作 → 放弃 MOVE_TO
        nobs, r, done, trunc, _info = env.step(a); tg = _info.get("terrain_grid"); traj["terrain_grid"].append(tg.tolist() if tg is not None and hasattr(tg, "tolist") else [])
        # 2026-08-26: 守卫战斗检测 — 真战斗 (character=savage 守卫 FIGHT, autofight 必胜)
        # 英雄进入守卫格 = 战斗打赢 = 守卫消失 (矿可占) → 首胜奖励 +100 (每局一次)
        if not guard_first_win:
            ah2 = int(nobs[3203]) if nobs[3203] >= 0 else 0
            b2 = 128 + ah2 * 26
            hx2, hy2 = int(nobs[b2+2]), int(nobs[b2+3])
            for (gx, gy, gz) in get_guards(args.mapname):
                if hx2 == gx and hy2 == gy:
                    r += 100.0  # 守卫战斗胜利 (首胜)
                    guard_first_win = True
                    if args.guard_done_steps > 0:
                        guard_done_countdown = args.guard_done_steps  # 启动终局倒计时 (新目标会重置)
                    print(f"[GUARD] guard ({gx},{gy}) fought & won at step {traj['steps']} +100", flush=True)
                    break
        # 2026-08-27 方案A: 守卫接近梯度 — 每接近守卫 1 格 +0.3 (净正, 压过 -0.1 步罚, 引导走向守卫)
        # get_guards 静态 vmap 位置; 英雄所在的守卫格 = 已清除 (战斗后守卫消失), 排除避免 min_d=0 恒
        _guards = get_guards(args.mapname)
        if _guards:
            _live = [(gx, gy) for (gx, gy, gz) in _guards if not (hx2 == gx and hy2 == gy)]
            if _live:
                _min_d = min(abs(hx2 - gx) + abs(hy2 - gy) for (gx, gy) in _live)
                if prev_guard_d is not None:
                    r += guard_grad_scale * (prev_guard_d - _min_d)  # P3: rate 可按图幅缩放 (默认 0.5 不变)
                prev_guard_d = _min_d
            else:
                prev_guard_d = None  # 无活守卫 (全部清除)
        else:
            prev_guard_d = None
        # === 2026-08-28 Level 3: 经济成型奖励 4 条 (非 T04 掩码屏蔽 16-21, 本段自动零触发) ===
        # 动作合法性由掩码保证 — 非法 16-21 不会被采样, 因此"动作被选" ≈ "动作合法可执行" ≈ 给奖励安全
        ah_e = int(nobs[3203]) if nobs[3203] >= 0 else 0
        b_e = 128 + ah_e * 26
        hx_e, hy_e = int(nobs[b_e+2]), int(nobs[b_e+3])
        # === 2026-08-29 T04 引导奖励: 首占矿 +N / 首进城镇 +N (复用守卫 +100 一次性事件模式) ===
        # T04 无守卫, 目标驱动源缺失 → 矿/城镇首访事件提供显式大额信号 (与守卫检测同款位置重合法)
        if args.objective_reward > 0:
            _mines, _towns = get_objectives(args.mapname)
            if not mine_taken and any(hx_e == _mx and hy_e == _my for (_mx, _my) in _mines):
                mine_taken = True
                r += args.objective_reward
                print(f"[MINE] mine captured at step {traj['steps']} +{args.objective_reward}", flush=True)
            if not town_visited and any(hx_e == _tx and hy_e == _ty for (_tx, _ty) in _towns):
                town_visited = True
                r += args.objective_reward
                print(f"[TOWN] town visited at step {traj['steps']} +{args.objective_reward}", flush=True)
        # --- 优先级3 (每步必算): 兵力power增量 × 0.001 (招兵→正; 战斗损耗→负不惩罚) ---
        # 5 army slots: field 10/12/14/16/18 = creature_id; 11/13/15/17/19 = count
        _slot_weights = [10, 40, 120, 350, 900]
        _army_now = 0.0
        for _si in range(5):
            try:
                _cnt = int(nobs[b_e + 11 + 2*_si])
                if _cnt > 0:
                    _army_now += _cnt * _slot_weights[_si]
            except:
                pass
        if econ_prev_army_power is not None:
            _dp = _army_now - econ_prev_army_power
            if _dp > 0:
                r += 0.001 * _dp
        econ_prev_army_power = _army_now
        # --- 优先级4 (前半): 首次踩资源点格 → 记步 ---
        _rpts = get_resource_points(args.mapname)
        if _rpts and econ_resource_step is None:
            if any(hx_e == _rx and hy_e == _ry for (_rx, _ry) in _rpts):
                econ_resource_step = traj["steps"]
        # --- 优先级1: 首 RECRUIT (16/17/18) 每档 +12 / 局 (2026-08-29 II.3 调优: +5→+12, 自主经济卡 0.6/局平台, 提高相对占矿+30 的吸引力) ---
        if a in (16, 17, 18) and not econ_recruit_first[a]:
            r += 12.0
            econ_recruit_first[a] = True
            print(f"[ECON] first RECRUIT tier={a-15} (act{a}) step {traj['steps']} +12", flush=True)
            # --- 优先级4 (后半): 资源→招兵 50步闭环 +15 / 局 ---
            if (not econ_closure_done) and econ_resource_step is not None:
                if (traj["steps"] - econ_resource_step) <= 50:
                    r += 15.0
                    econ_closure_done = True
                    print(f"[ECON] closure (resource→recruit {traj['steps']-econ_resource_step}s) step {traj['steps']} +15", flush=True)
        # --- 优先级2: 首 BUILD_2 (兵种建筑, 动作20) +15 / 局 (2026-08-29 II.3 调优: +8→+15) ---
        if a == 20 and not econ_build2_done:
            r += 15.0
            econ_build2_done = True
            print(f"[ECON] first BUILD_2 (creature dwelling, act20) step {traj['steps']} +15", flush=True)
        if cycle_penalty != 0.0:
            r += cycle_penalty  # 状态级循环惩罚 (第5轮)
        # === 动作级循环惩罚 (2026-08-19 第7轮): 连续 N 步重复 / 固定两两交替 → 负 reward ===
        # 治 [3,7,3,7]/[2,6,2,6]/[4,2,7,4,2,7]/[2,2,2,2] 死循环 — 状态级(同pos≥5)与横跳(prev2)
        # 只抓位置往返, 抓不住推进型动作循环 (位置持续变化但动作模式固定); 强制阶段(24)不检测
        # 第7轮 v2: 剔除 10 (END_TURN) — 3.0 诱发 [走,走,10] 穿插投机 (10 前2次免费, 永不触 -5),
        # 插入 10 会打断检测窗口; 剔除后 10 无法逃避检测, 投机失去收益
        if a != 10:
            act_hist.append(a)
        if args.act_loop_penalty > 0 and traj["steps"] >= args.move_to_force:
            if len(act_hist) >= args.act_loop_repeat and len(set(act_hist[-args.act_loop_repeat:])) == 1:
                r -= abs(args.act_loop_penalty)
            elif len(act_hist) >= args.act_loop_alt:
                tail = act_hist[-args.act_loop_alt:]
                if len(set(tail[::2])) == 1 and len(set(tail[1::2])) == 1 and tail[0] != tail[1]:
                    r -= abs(args.act_loop_penalty)
            # P3: 三阶周期 [a,b,c,a,b,c,a,b,c]
            elif len(act_hist) >= args.act_loop_p3:
                tail = act_hist[-args.act_loop_p3:]
                if (len(set(tail[::3])) == 1 and len(set(tail[1::3])) == 1
                        and len(set(tail[2::3])) == 1
                        and len({tail[0], tail[1], tail[2]}) == 3):
                    r -= abs(args.act_loop_penalty)
        if args.move_to_test:
            a = 24
        interact_streak = interact_streak + 1 if a == 8 else 0
        endturn_streak = endturn_streak + 1 if a == 10 else 0
        # 非法方向惩扣：move 后英雄位置没变（服务器拒绝），给 -0.5
        if a < 8 and traj["steps"] > 0:
            # B 态势感知: 用 active_hero (obs[3203]) 定位当前英雄, heroes 段起点 128, 每英雄 26 字段 (OBS v3), pos 在字段 2,3,4
            ah = int(nobs[3203]) if nobs[3203] >= 0 else 0
            base = 128 + ah * 26
            prev_pos = (int(traj["obs"][-1][base+2]), int(traj["obs"][-1][base+3]), int(traj["obs"][-1][base+4]))
            cur_pos = (int(nobs[base+2]), int(nobs[base+3]), int(nobs[base+4]))
            if prev_pos == cur_pos:
                r = -0.5
            # 横跳惩罚 (2026-08-19): 回到两格前位置 = 往返打转 (局部最优), 额外 -2.0
            if len(traj["obs"]) >= 2:
                prev2 = traj["obs"][-2]
                ah2 = int(prev2[3203]) if prev2[3203] >= 0 else 0
                base2 = 128 + ah2 * 26
                prev2_pos = (int(prev2[base2+2]), int(prev2[base2+3]), int(prev2[base2+4]))
                if cur_pos == prev2_pos:
                    r -= 2.0
            # 两格往返加强 (2026-08-25): 8 步窗英雄位置仅 2 格交替 → 额外 -3.0 + 强制随机方向
            # 背景: 横跳 -2.0 被探索奖励 (NK2 3x3 邻域 ×0.2) 掩盖 (净 -0.5), 模型持续横跳
            # 强制阶段 (MOVE_TO 展开的往返=绕障碍正常行为) 不检测, 与 act_loop 一致
            if len(traj["obs"]) >= 8 and traj["steps"] >= args.move_to_force:
                recent = []
                for o in traj["obs"][-8:]:
                    a2 = int(o[3203]) if o[3203] >= 0 else 0
                    b2 = 128 + a2 * 26
                    recent.append((int(o[b2+2]), int(o[b2+3])))
                if len(set(recent)) <= 2:
                    r -= 3.0
                    if force_dir is None:
                        dirs = [d for d in range(8) if bool(passable[d])]
                        if dirs:
                            force_dir = random.choice(dirs)
        traj["obs"].append(obs.tolist())
        traj["act"].append(a)
        traj["rew"].append(float(r))
        traj["nobs"].append(nobs.tolist())
        traj["done"].append(bool(done or trunc))
        traj["steps"] += 1
        traj["total_rew"] = sum(traj["rew"])
        # 每步增量写入：进程崩溃也能保留已收集的数据
        with open(args.outfile, "w") as f:
            json.dump(traj, f); f.flush(); os.fsync(f.fileno())
        obs = nobs
        if done or trunc: break
        # 2026-08-28: 僵尸段终局 — 全堵(英雄死亡)连续 2 步 → 标记 done 并退出。
        # 背景: 英雄死后 8 方向 passable 全 0, 走 a=10 旁路 (绕过 END_TURN 冷却 mask)
        # 无限刷到 200 步上限。危害: ①白跑 60-140 僵尸步 ②done=False 进 buffer,
        # GAE 穿过死亡点 bootstrap, -700 冲击污染整条轨迹价值学习 (vloss 不降主因之一)
        zombie_streak = zombie_streak + 1 if zombie else 0
        if zombie_streak >= 2:
            traj["done"][-1] = True
            print(f"[ZOMBIE] hero dead (all-blocked x{zombie_streak}), end ep at step {traj['steps']}", flush=True)
            break
        # 2026-08-28 BND-20260828-02: END_TURN 连喷 ≥30 独立兜底 (zombie 双保险)。
        # endturn_streak L425 对旁路直接赋值的 a=10 也会计数, 但 L215 的 logits mask 用不到
        # (旁路不走 logits), 所以单独用它做 30 次熔断, 防未来新旁路又忘了标 zombie=True。
        if endturn_streak >= 30:
            traj["done"][-1] = True
            print(f"[ENDTURN_FUSE] act10 x{endturn_streak} fuse-break, end ep at step {traj['steps']}", flush=True)
            break
        # 2026-08-29: 守卫击杀自动终局 — +100 后 N 步内无新目标 → 提前结束。
        # 背景: 杀守卫后英雄存活无终局信号 → 长期振荡 (每步 -0.1 + 循环惩罚) 烧穿 +100,
        # final r 跌破 80 晋级线 → 20X20_01 全 0 胜。获取新目标 (守卫/矿/资源) 时倒计时重置。
        if guard_done_countdown is not None:
            guard_done_countdown -= 1
            if guard_done_countdown <= 0:
                traj["done"][-1] = True
                print(f"[GUARD_DONE] no new objective in {args.guard_done_steps} steps after guard win, end ep at step {traj['steps']}", flush=True)
                break
        if args.model and traj["steps"] >= args.max_turns:
            break
except Exception as e:
    traj["error"] = str(e)
    # 即使异常也写一次（segfault 无法被 Python 捕获，但 OSError/Timeout 等可以）
    try:
        with open(args.outfile, "w") as f:
            json.dump(traj, f); f.flush(); os.fsync(f.fileno())
    except: pass

# 最终写入（正常退出时覆盖，确保完整数据）
with open(args.outfile, "w") as f:
    json.dump(traj, f); f.flush(); os.fsync(f.fileno())
os._exit(0)
