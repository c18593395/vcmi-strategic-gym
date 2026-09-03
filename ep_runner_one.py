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
            # 2026-08-31 TOWN 轴修复: 过滤我方城 (训练方=red, owner 在 options.owner) —
            # 己方城 step0 即在身旁, 计入会使 [TOWN]+30 变免费糖; 只保留 blue/中立城
            towns = []
            for k, o in objs.items():
                if k.startswith("town_"):
                    _own = str(o.get("options", {}).get("owner", "")).lower()
                    if _own == "red":
                        continue
                    towns.append((int(o["x"]), int(o["y"])))
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

# 2026-09-01 改法一 (城镇轴 greedy→全图 BFS): 修 greedy 寻路陷阱 —
# 20X20_02 (岩石簇 9-10,2-5 / 15-17,10-11 卡死 greedy → TOWN_BLOCKED 100%) 与 30X30_01 (岩石簇 16-19,10-11) 同时受益。
# 通行性静态源 = vmap surface_terrain.json (rc00_ 岩石不可走; wa 前缀水体不可走), 地形每局不变 → 按 mapname 缓存
_PASS_CACHE = {}
def get_passable_grid(mapname):
    """全图通行性 bool 矩阵 grid[y][x] (True=可走); 读取失败返回 None (调用方退回原局部 BFS/贪心)"""
    if mapname not in _PASS_CACHE:
        try:
            p = f"/mnt/d/Bigdata/hero3_fresh/maps/training/{mapname}"
            with zipfile.ZipFile(p) as z:
                terr = json.loads(z.read("surface_terrain.json"))
            _h, _w = len(terr), len(terr[0])
            grid = np.ones((_h, _w), dtype=bool)
            for _y in range(_h):
                for _x in range(_w):
                    _c = str(terr[_y][_x])
                    if _c.startswith("rc") or _c.startswith("wa"):  # rock / water
                        grid[_y][_x] = False
            _PASS_CACHE[mapname] = grid
        except Exception:
            _PASS_CACHE[mapname] = None
    return _PASS_CACHE[mapname]

def bfs_full_dir(mapname, hx, hy, tx, ty, blocked=None):
    """全图 BFS (8 邻, 对角禁穿双岩角 — 与引擎行进规则一致), 返回 (第一步方向动作码 0-7, 路径步数)。
    不可达 / 无地形数据 → (None, -1)
    blocked: 本局动态障碍格集合 (敌方英雄等, 引擎实时拒绝通过的格) — 地形层 BFS 看不见, 需外部喂
    2026-09-02 晚修复 (21 次全弃真因): 城格 pas=0 (visitable-not-standable, 引擎禁踩),
    旧版目标格不可走 → 直接结构性不可达 → start_home/占城引导/回城取兵三处城目标恒判死 →
    贪心裸奔 hero 徘徊城外 2 格 TOWNSTALL fuse。现降级: 目标 8 邻可站格作代理目标 (多目标
    BFS 最近者), 邻接即达 — 与 start_home adjacent / 引擎 visitablePos Chebyshev≤1 口径一致"""
    grid = get_passable_grid(mapname)
    if grid is None:
        return None, -1
    H, W = grid.shape
    if not (0 <= tx < W and 0 <= ty < H):
        return None, -1
    targets = [(tx, ty)] if grid[ty][tx] else []
    if not targets:
        for _ddx, _ddy in _DIRS:
            _nx, _ny = tx + _ddx, ty + _ddy
            if 0 <= _nx < W and 0 <= _ny < H and grid[_ny][_nx]:
                targets.append((_nx, _ny))
        if not targets:
            return None, -1  # 城被围死 (8 邻全不可站) → 真不可达
        if any(hx == _sx and hy == _sy for _sx, _sy in targets):
            return None, 0   # hero 已在可站邻格 (= 已邻接), plen=0 供卡死判定递减
    if hx == tx and hy == ty:
        return None, -1  # 已到达
    prev = {(hx, hy): None}
    q = deque([(hx, hy)])
    _tgt_set = set(targets)
    while q:
        cx, cy = q.popleft()
        if (cx, cy) in _tgt_set:
            break
        for d, (ddx, ddy) in enumerate(_DIRS):
            nx, ny = cx + ddx, cy + ddy
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in prev and grid[ny][nx]:
                if blocked and (nx, ny) in blocked:
                    continue  # 2026-09-01 改法三: 动态障碍格 (敌方英雄) 视为不可通行
                if ddx != 0 and ddy != 0 and not (grid[cy][nx] or grid[ny][cx]):
                    continue  # 对角穿角禁行 (两正交邻格全堵时不许斜穿)
                prev[(nx, ny)] = ((cx, cy), d)
                q.append((nx, ny))
    _hit = next((p for p in _tgt_set if p in prev), None)
    if _hit is None:
        return None, -1
    cur, first, plen = _hit, None, 0
    while prev[cur] is not None:
        cur, d0 = prev[cur]
        first = d0
        plen += 1
    return first, plen

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
    move_town_bfs = False    # 2026-09-01 改法二: 当前目标是否 BFS 引导城镇 (blue城/回城取兵) — 卡死判定用 BFS plen
    dyn_blocked = set()      # 2026-09-01 改法三: 本局动态障碍格 (敌方英雄堵路时实探记录) — BFS 绕行用
    # 2026-08-29 II.3 调优: 每次执行小额奖励的计数器 (保险丝 每档/局上限 5 次)
    econ_recruit_count = {16: 0, 17: 0, 18: 0}
    econ_build2_count = 0
    # 2026-08-31 回城取兵引导: 英雄 visit 己方城 → 强制 RECRUIT 窗 (兵直上英雄部队)
    # 机制: C++ RECRUIT dst = town->getUpperArmy() = visiting hero → visit 状态招兵直接进英雄 5 槽
    # → 兵力增量奖励 0.01×dp 立刻生效 (此前招兵进城 garrison, 该奖励管道对 RECRUIT 是断的)
    visit_econ_steps = 0     # 剩余取兵窗步数 (触发=4 步 16/17/18 轮换)
    visit_econ_cooldown = 0  # 冷却 (窗结束/触发后 30 步内不再触发, 防锁死城内 spam 招 0)
    start_home = True        # 2026-09-02 出发前招兵阶段: 每局开局先回城招兵带兵再探索 (用户设计)
    own_town_guiding = False # 取兵引导状态 (边沿检测: 启动瞬间打诊断日志用)
    own_town_guide_count = 0 # 诊断日志限次 (每局上限 5 条防刷屏)

    def _towns_dump(obs):
        # [START_HOME] begin/abort 诊断 (09-02 晚): 8 城段全转储 (id,owner,x,y) —
        # 一次看清 obs 里到底有哪些城 / owner 语义 (嫌疑: T04 敌方目标城 owner 被 obs 标 0,
        # start_home 把敌城当己方城引导 hero 奔过去, visit 敌城 +30 后终局, 招兵分支 0 进入)
        parts = []
        for _ti in range(8):
            _tb = 336 + _ti * 18
            if int(obs[_tb+2]) > 0 or int(obs[_tb+3]) > 0:  # pos 非零 = 有效槽 (与选城判据一致)
                parts.append(f"id{int(obs[_tb])}o{int(obs[_tb+1])}@({int(obs[_tb+2])},{int(obs[_tb+3])})")
        return " ".join(parts) if parts else "NONE"
    # 08-31 占城观测埋点 (只观测不改奖励): 蓝城 owner 1→0 事件
    town_owner_init = None   # {town_id: owner} 首步快照
    town_capture_logged = set()  # 已记录捕获的城 id
    recruit_mask_prev = {}   # 08-31 S1 建设观测: {town_id: 上一步 recruit_mask} — 位增 = 新巢穴建成
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
        # 2026-08-31 回城取兵检测: 英雄位于己方城 (dist<=1) → 启动 4 步 RECRUIT 窗 (带 30 步冷却防 spam)
        # 己方城识别: obs towns 段 [336+ti*18], owner==0 (红方) + pos 非零 (空槽全 0 排除)
        # 触发信号 = recruit_mask 非零 (城有巢穴可招) — garrison 字段 C++ fill 恒 0 (strategic_state.cpp L724 memset, 未实现), 不可用
        # 关键机制: visit 状态 RECRUIT dst=getUpperArmy()=英雄 → 新招兵直上部队, 无需 garrison 存量
        if visit_econ_cooldown > 0:
            visit_econ_cooldown -= 1
        if args.objective_reward > 0 and red_model is not None and visit_econ_steps <= 0 and visit_econ_cooldown <= 0:
            try:
                _ah0 = int(obs[3203]) if obs[3203] >= 0 else 0
                _hb0 = 128 + _ah0 * 26
                _hx0, _hy0 = int(obs[_hb0+2]), int(obs[_hb0+3])
                for _ti0 in range(8):
                    _tb0 = 336 + _ti0 * 18
                    if int(obs[_tb0+1]) == 0 and (int(obs[_tb0+2]) > 0 or int(obs[_tb0+3]) > 0):
                        if abs(_hx0 - int(obs[_tb0+2])) <= 1 and abs(_hy0 - int(obs[_tb0+3])) <= 1:
                            _rm0 = int(obs[_tb0+14]) | int(obs[_tb0+15])
                            if _rm0 > 0:
                                visit_econ_steps = 4
                                print(f"[TOWN_VISIT] own town recruit window at step {traj['steps']} recruit_mask={_rm0}", flush=True)
                            break
            except Exception:
                pass
        # 经济动作采样强制 (2026-08-24 Level 3): 每局前 N 步强制 16-21 轮换 (RECRUIT/BUILD 引导)
        # 模型从未见过这些码 → logits 极负 → bias 无效, 采样强制 (move_to_force 同款教训)
        # 2026-08-29 B 方案"每日提醒": 前 N 步连续强制后, 每 40 步插入 4 步经济轮换 —
        # 自主 16-21 卡 0.6/局平台 90+ 局 (强制期外无任何经济提示), 周期体验提升梯度密度;
        # [ECON] first 奖励只发每档一次, 周期插入不放大奖励, 供体验 + 配合兵力增量信号 (0.01)
        econ_force_now = False
        if args.economy_force > 0 and red_model is not None:
            if traj["steps"] < args.economy_force:
                econ_force_now = True
            elif (traj["steps"] - args.economy_force) % 40 < 4:
                econ_force_now = True  # "每日提醒": 每 40 步 4 步经济窗 (~10% 体验占比)
            if econ_force_now:
                econ_acts = [16, 17, 18, 19, 20, 21]  # RECRUIT_1/2/3, BUILD_1/2/3 轮换
                a = econ_acts[traj["steps"] % len(econ_acts)]
        # 2026-08-31 回城取兵窗 (最高优先覆盖): 强制 RECRUIT 轮换 — visit 己方城时招兵直上英雄部队
        if visit_econ_steps > 0:
            a = [16, 17, 18][traj["steps"] % 3]
            visit_econ_steps -= 1
            if visit_econ_steps == 0:
                visit_econ_cooldown = 30
        # 2026-09-02 出发前招兵 (用户设计, 每局确定性): 先回城招兵带兵再探索 —
        # 英雄未邻接己方城时强制 MOVE_TO 己方城 (move_town_bfs 引导); 邻接后交由
        # 上方 visit 检测开取兵窗 (16/17/18), 引擎 P1/P1b 完成 visit+招兵直上英雄;
        # 取兵窗结束 (visit_econ_steps 归零) 本阶段自动解除 → 正常探索.
        # 终止保险: 无己方城 / 步数 > 80 放弃 (远图不无限烧步); 邻接开局 (20X20) 直接触发取兵窗
        if start_home and args.objective_reward > 0 and red_model is not None and visit_econ_steps <= 0:
            _ah2 = int(obs[3203]) if obs[3203] >= 0 else 0
            _hb2 = 128 + _ah2 * 26
            _hx2, _hy2, _hz2 = int(obs[_hb2+2]), int(obs[_hb2+3]), int(obs[_hb2+4])
            _own = None
            for _ti2 in range(8):
                _tb2 = 336 + _ti2 * 18
                if int(obs[_tb2+1]) == 0 and (int(obs[_tb2+2]) > 0 or int(obs[_tb2+3]) > 0):
                    _own = (int(obs[_tb2+2]), int(obs[_tb2+3]))
                    break
            if traj["steps"] == 0:
                # [START_HOME] begin: 首拍全城段转储 — 坐实 obs owner 语义 (嫌疑: T04 敌方目标城 owner 被标 0)
                print(f"[START_HOME] begin step=0 hero=({_hx2},{_hy2}) towns=[{_towns_dump(obs)}]", flush=True)
            if _own is None or traj["steps"] > 80:
                _why = "no_own_town" if _own is None else "timeout>80"
                start_home = False  # 无己方城 / 超时放弃
                print(f"[START_HOME] abort({_why}) at step {traj['steps']} own={_own} hero=({_hx2},{_hy2}) towns=[{_towns_dump(obs)}]", flush=True)
            elif max(abs(_own[0] - _hx2), abs(_own[1] - _hy2)) <= 1:
                start_home = False      # 已邻接 → visit 检测下拍开取兵窗 (冷却保持, 防 spam)
                print(f"[START_HOME] adjacent at step {traj['steps']} own={_own} hero=({_hx2},{_hy2})", flush=True)
            else:
                if traj["steps"] == 0 or (not move_target) or (move_target and (move_target[0] != _own[0] or move_target[1] != _own[1])):
                    print(f"[START_HOME] guide own={_own} hero=({_hx2},{_hy2}) at step {traj['steps']}", flush=True)
                a = 24  # 强制回城, 覆盖 economy_force (远距离招兵在邻接守卫下只会空转)
                move_target = (_own[0], _own[1], _hz2)
                move_guard_target = False
                move_town_target = False
                move_town_bfs = True
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
                # 2026-09-01 改法四: 城镇目标邻接即到达 — 引擎禁踩城格 (城格 pas=0, visitable-not-standable),
                # 旧判定要求 dist==0 踩上城格 → 邻格恒 stall + 把目标城格误入 dyn_blocked 黑名单 (自毁目标);
                # 判距口径 = 切比雪夫 (8邻) 与 TOWN/TOWN_VISIT 判定一致 — 曼哈顿会漏对角邻格
                # (复现: hero(3,3) tgt(2,2) 曼哈顿=2 不清目标 → 停滞废弃, 取兵窗开了兵没取)
                if move_town_bfs and max(abs(tx - hx), abs(ty - hy)) <= 1:
                    move_target = None
                    move_guard_target = False
                    move_town_target = False
                    move_town_bfs = False
                elif tx is None or (abs(tx - hx) + abs(ty - hy) == 0):
                    if tx is not None:
                        move_target = None  # 已到达
                        move_guard_target = False
                        move_town_target = False
                        move_town_bfs = False
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
                    # 2026-09-01 改法二: BFS 引导城镇目标 (blue城 / 己方取兵城) — 卡死判定用 BFS plen
                    move_town_bfs = move_town_target or any(
                        (tx == int(obs[336 + _ti * 18 + 2]) and ty == int(obs[336 + _ti * 18 + 3]))
                        for _ti in range(8) if int(obs[336 + _ti * 18 + 1]) == 0)
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
                # 2026-08-31 TOWN 轴引导恢复: 矿占完后引导最近非我方城 (占城 = 1v7 终极目标语义) —
                # 约束防卡死复发 (此前 324 次 [TOWN_BLOCKED] 教训): ① 只在 mine_taken 后启用 (先经济后占城)
                # ② 不设距离上限 — blue 城全在对角远端 (20X20 图 hero→城 ~22 格, 30X30 ~42), dist<=20 会让轴再死;
                #    远城贪心失败由 move_stall (6步) + town_blocked 本局禁用兜底, 每局学费上限 6 步 vs first +30
                # ③ first-only +30 天然限收益
                town_best = None
                if args.objective_reward > 0 and mine_taken and not town_blocked and not town_visited:
                    # 2026-09-01 改法一: 选址从 greedy Manhattan 改为全图 BFS —
                    # ① 不可达的城直接跳过 (不设目标 → 不烧 6 步学费, [TOWN_BLOCKED] 不再触发);
                    # ② 可达的城按真实路径步数取最近 (绕岩石后 Manhattan 近的未必真近)
                    for (_tx, _ty) in get_objectives(args.mapname)[1]:
                        _dir, _plen = bfs_full_dir(args.mapname, hx, hy, _tx, _ty, blocked=dyn_blocked)
                        if _dir is None:
                            continue
                        if town_best is None or _plen < town_best[0]:
                            town_best = (_plen, _tx, _ty)
                # 2026-08-31 回城取兵引导: 己方城 recruit_mask 非零 (有巢穴可招) → 引导 MOVE_TO 己方城
                # (visit 后取兵窗发 RECRUIT, 新兵直上英雄部队)
                # 优先级 = 守卫 > 矿 > 回城取兵 > blue城占城 > 资源堆 (取兵高频+近城, 战力成长是 1v7 核心);
                # 触发信号 = recruit_mask (C++ fill_v3_fields 填充) — garrison 字段 C++ 恒 0 未实现, 不可用;
                # 约束: dist<=25 (取兵是常规行为不该跨图跑) ; 卡死由 move_stall 通用放弃 (目标可反复出现, 不禁用)
                own_town_best = None
                if args.objective_reward > 0:
                    for _ti1 in range(8):
                        _tb1 = 336 + _ti1 * 18
                        if int(obs[_tb1+1]) == 0 and (int(obs[_tb1+2]) > 0 or int(obs[_tb1+3]) > 0):
                            _rm1 = int(obs[_tb1+14]) | int(obs[_tb1+15])
                            if _rm1 > 0:
                                _od1 = abs(int(obs[_tb1+2]) - hx) + abs(int(obs[_tb1+3]) - hy)
                                # 2026-09-01 改法一: 可达性过滤 (BFS 不可达 → 不引导, 防 greedy 卡死烧 move_stall)
                                _d1, _ = bfs_full_dir(args.mapname, hx, hy, int(obs[_tb1+2]), int(obs[_tb1+3]), blocked=dyn_blocked)
                                if _od1 <= 25 and _od1 > 0 and _d1 is not None and (own_town_best is None or _od1 < own_town_best[0]):
                                    own_town_best = (_od1, int(obs[_tb1+2]), int(obs[_tb1+3]))
                    # 诊断日志 (边沿触发): 区分"引导没启动"(此条不打) vs "启动了没走到"(打了但无 [TOWN_VISIT])
                    if own_town_best is not None:
                        if not own_town_guiding:
                            own_town_guiding = True
                            if own_town_guide_count < 5:
                                print(f"[OWN_TOWN_GUIDE] garrison pickup guide started dist={own_town_best[0]} at step {traj['steps']}", flush=True)
                            own_town_guide_count += 1
                    else:
                        own_town_guiding = False
                elif own_town_guiding:
                    own_town_guiding = False
                if guard_best is not None:
                    tx, ty, tz = guard_best[1], guard_best[2], hz
                    next_dir_idx = -1  # 无 C++ next_dir → 走 BFS/贪心
                    move_target = (tx, ty, tz)
                    move_stall = 0
                    move_guard_target = True  # 2026-08-25: 守卫格 passable=0 (blocked), 需跳过 passable 检查
                    move_town_target = False
                    move_town_bfs = False
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
                    move_town_bfs = False
                    if guard_done_countdown is not None:
                        guard_done_countdown = args.guard_done_steps
                elif own_town_best is not None:
                    # 2026-08-31 回城取兵分支: 到达后 visit 检测块自动开取兵窗 (RECRUIT 兵直上英雄)
                    # move_town_target=False — 己方城卡死只走通用 move_stall 放弃, 不触发 town_blocked (blue城专用)
                    # move_town_bfs=True — 改法二: 取兵城同为 BFS 引导, 卡死判定用 BFS plen (修绕岩误判)
                    tx, ty, tz = own_town_best[1], own_town_best[2], hz
                    next_dir_idx = -1
                    move_target = (tx, ty, tz)
                    move_stall = 0
                    move_guard_target = False
                    move_town_target = False
                    move_town_bfs = True
                    if guard_done_countdown is not None:
                        guard_done_countdown = args.guard_done_steps
                elif town_best is not None:
                    # 2026-08-31 TOWN 引导分支: 优先级 = 守卫 > 矿 > 城 > 资源堆 —
                    # 城不在 target_list (C++ 不填) → next_dir_idx=-1 走 Python BFS/贪心; move_town_target=True 启用卡死兜底
                    tx, ty, tz = town_best[1], town_best[2], hz
                    next_dir_idx = -1
                    move_target = (tx, ty, tz)
                    move_stall = 0
                    move_guard_target = False
                    move_town_target = True
                    move_town_bfs = True
                    if guard_done_countdown is not None:
                        guard_done_countdown = args.guard_done_steps
                elif best is not None:
                    tx, ty, tz = int(best[2]), int(best[3]), int(best[4])
                    move_target = (tx, ty, tz)
                    move_stall = 0
                    move_guard_target = False
                    move_town_target = False
                    move_town_bfs = False
                    if guard_done_countdown is not None:
                        guard_done_countdown = args.guard_done_steps  # 新目标 (矿/资源) → 重置倒计时
                else:
                    move_target = None
                    move_guard_target = False
                    move_town_target = False
                    move_town_bfs = False
            if tx is not None:
                # Phase I.2: 优先用 C++ 全图 BFS (obs[3330:3338] = next_dir[8])
                nd = int(obs[3330 + next_dir_idx]) if next_dir_idx >= 0 else -1
                if nd >= 0:
                    a = nd
                else:
                    # 2026-09-01 改法一: 城镇目标 (nd<0 非守卫) 先走全图 BFS 绕岩石, 失败再退 15×15 局部 BFS → 贪心
                    if not move_guard_target:
                        _fd, _ = bfs_full_dir(args.mapname, hx, hy, tx, ty, blocked=dyn_blocked)
                        if _fd is not None:
                            a = _fd
                    # 回退: 旧 15×15 BFS (守卫目标跳过 — BFS 按可通行性会绕开守卫格)
                    if not move_guard_target and (a < 0 or a > 7):
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
                # 卡住检测: 连续 6 步进度不减小 → 放弃换目标 (被堵/绕路)
                # 2026-09-01 改法二: BFS 引导的城镇目标 (blue城/回城取兵) 改用 BFS 剩余路径长度判进度 —
                # 绕岩路径前段曼哈顿不降反升, 旧判定 6 步即误判 TOWN_BLOCKED (重启后 6/10 局误触发 →
                # 占城引导被禁 → 200 步超时深负, avg_r 被压 0 的主因);
                # BFS plen 持续下降 = 合法绕行不误杀; 位置不动/原地打转 plen 不减 = 真卡死;
                # BFS 不可达 (返回 -1) 回退曼哈顿 → 真不可达照常触发兜底放弃
                if move_town_bfs:
                    _plen_now = bfs_full_dir(args.mapname, hx, hy, tx, ty, blocked=dyn_blocked)[1]
                    cur_dist = _plen_now if _plen_now >= 0 else abs(tx - hx) + abs(ty - hy)
                else:
                    cur_dist = abs(tx - hx) + abs(ty - hy)
                if cur_dist >= move_stall_prev:
                    move_stall += 1
                    # 2026-09-01 改法三: 停滞 = BFS 首步格被引擎拒绝 (实探: 敌方英雄等动态障碍) —
                    # 把该格记入本局黑名单, 后续 BFS 重规划绕行; 诊断埋点打印阻挡格
                    if move_town_bfs and move_stall == 1:
                        _sdir, _ = bfs_full_dir(args.mapname, hx, hy, tx, ty, blocked=dyn_blocked)
                        _bx, _by = -1, -1
                        if _sdir is not None:
                            _bx, _by = hx + _DIRS[_sdir][0], hy + _DIRS[_sdir][1]
                            if (_bx, _by) != (tx, ty):  # 目标格本身 (城格 visitable) 不入黑名单, 防自毁目标
                                dyn_blocked.add((_bx, _by))
                        print(f"[TOWNSTALL] hero=({hx},{hy}) tgt=({tx},{ty}) plen={cur_dist} block=({_bx},{_by}) pas={[int(x) for x in obs[3211:3219]]}", flush=True)
                else:
                    move_stall = 0
                move_stall_prev = cur_dist
                if move_stall >= 6:
                    if move_town_target and args.objective_reward > 0 and not town_blocked:
                        town_blocked = True  # 城镇 BFS 进度真卡死 → 本局禁用城优先, 防无限卡城循环
                        print(f"[TOWN_BLOCKED] town BFS progress stalled at step {traj['steps']} hero=({hx},{hy}) tgt=({tx},{ty})", flush=True)
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
            # 2026-08-31 TOWN 判定修复: 精确站上城格 → dist<=1 (8邻+自身) —
            # 根因 (结构性): 城格 template mask 中心 'A'=actionable+blocking, 英雄访问停在邻格,
            # 英雄坐标结构性不可能等于城坐标 → ==判定永假 (1850 局 0 次).
            # 防假糖: first-only (每局一次) + 我方城已过滤 (get_objectives)
            _tow_owner = None
            if not town_visited:
                for _tx, _ty in _towns:
                    if abs(hx_e - _tx) <= 1 and abs(hy_e - _ty) <= 1:
                        # 08-31 埋点②: 记录被访问城的 owner (验证 visited 糖真假: owner=blue 路过 / red 真占领)
                        for _ti9 in range(8):
                            _tb9 = 336 + _ti9 * 18
                            if int(obs[_tb9]) > 0 and int(obs[_tb9+2]) == _tx and int(obs[_tb9+3]) == _ty:
                                _tow_owner = int(obs[_tb9+1])
                                break
                        town_visited = True
                        r += args.objective_reward
                        _ow_tag = 'captured' if _tow_owner == 0 else f'enemy-held({_tow_owner})'
                        print(f"[TOWN] town visited at step {traj['steps']} +{args.objective_reward} owner={_ow_tag}", flush=True)
                        break
            # 08-31 埋点①: 占城观测 (只观测不改奖励) — 蓝城 owner 1→0 = 真占领事件
            # 占城率 = grep [TOWN_CAPTURE] 次数/局数; R6 修复前若占城需战斗则恒 0 (基线数据)
            if red_model is not None:
                try:
                    _own_map = {}
                    for _ti8 in range(8):
                        _tb8 = 336 + _ti8 * 18
                        _tid8 = int(obs[_tb8])
                        if _tid8 > 0:
                            _own_map[_tid8] = int(obs[_tb8+1])
                    if town_owner_init is None:
                        town_owner_init = _own_map
                    else:
                        for _tid9, _ow9 in _own_map.items():
                            if _tid9 not in town_capture_logged and town_owner_init.get(_tid9) == 1 and _ow9 == 0:
                                town_capture_logged.add(_tid9)
                                print(f"[TOWN_CAPTURE] blue town id={_tid9} owner 1->0 at step {traj['steps']} (observe only, no reward)", flush=True)
                except Exception:
                    pass
                # 08-31 撤梯子③-S1 建设观测 (只观测不加奖): 己方城 recruit_mask 位增 = 新巢穴建成
                # S2/S3 建设奖的基线数据源 (触发频率/每局次数)
                for _ti7 in range(8):
                    _tb7 = 336 + _ti7 * 18
                    _tid7 = int(obs[_tb7])
                    if _tid7 > 0 and int(obs[_tb7+1]) == 0:  # 己方城
                        _rm7 = int(obs[_tb7+14]) | int(obs[_tb7+15])
                        _prev7 = recruit_mask_prev.get(_tid7)
                        if _prev7 is not None and (_rm7 & ~_prev7 & 0xFFFF):
                            print(f"[BUILD_NEW] own town id={_tid7} new dwelling bits={_rm7 & ~_prev7 & 0xFFFF:#06x} at step {traj['steps']} (observe only)", flush=True)
                        recruit_mask_prev[_tid7] = _rm7
        # --- 优先级3 (每步必算): 兵力power增量 × 0.01 (招兵→正; 战斗损耗→负不惩罚) ---
        # 2026-08-29 B 方案: 0.001→0.01 — 招 1 个 tier0 兵 (value 10) 原 +0.01 不可见, 现 +0.1;
        # 高级兵价值 900 → +9.0, 与 RECRUIT +12 同量级, 让"招到兵"有可学习信号 (战损负向同步放大, 促进避战保兵)
        # (旧注释 "5 slots field 10-19 id+count 交错" 是错误布局假设, 已废弃 — 见下方 P2 注)
        # 2026-09-01 P2 取兵链路: obs 英雄槽真实布局 = army 7 个纯 count 在 field 15-21
        # (strategic_env.py _build_obs: 无 creature_id 字段); 旧读法 11-19 混入 knowledge/max_mana
        # 且假设 id+count 交错布局 — 全错位, 导致 [RECRUITED]/兵力增量奖励恒失效。
        # 权重沿用 VCMI AI value 阶梯 (T1-T5), T6/T7 外推
        _slot_weights = [10, 40, 120, 350, 900, 1600, 2500]
        _army_now = 0.0
        for _si in range(7):
            try:
                _cnt = int(nobs[b_e + 15 + _si])
                if _cnt > 0:
                    _army_now += _cnt * _slot_weights[_si]
            except:
                pass
        if econ_prev_army_power is not None:
            _dp = _army_now - econ_prev_army_power
            if _dp > 0:
                r += 0.02 * _dp
                # 08-31 S1 招兵效果观测 (只观测): dp>0 = 兵力上英雄 (取兵链路/城内招兵)
                print(f"[RECRUITED] army power +{_dp:.0f} at step {traj['steps']} (observe only)", flush=True)
        econ_prev_army_power = _army_now
        # --- 优先级4 (前半): 首次踩资源点格 → 记步 ---
        _rpts = get_resource_points(args.mapname)
        if _rpts and econ_resource_step is None:
            if any(hx_e == _rx and hy_e == _ry for (_rx, _ry) in _rpts):
                econ_resource_step = traj["steps"]
        # --- 优先级1: RECRUIT (16/17/18) first 每档 +12 + 每次执行小额 (2026-08-29 II.3 调优) ---
        # first 大额引导 (被 economy_force 强制期消费属预期); 每次小额 = 自主通道的持续即时信号
        # 保险丝: 每档每局上限 5 次发奖 (防 spam; 资源/每周兵量天然封顶)
        # 2026-08-29 撤梯子②: 每次 +2→+1; 2026-08-31 撤梯子③-S1: +1→+0.5 (递归半价, 每窗 x0.5 直至实质归零;
        #   同步兵力系数 0.01→0.02 + 效果观测 [RECRUITED]/[BUILD_NEW] — 糖减半效果信号翻倍, 总激励平滑迁移)
        if a in (16, 17, 18):
            econ_recruit_count[a] += 1
            _rc_rewarded = econ_recruit_count[a] <= 5
            if _rc_rewarded:
                r += 0.5
            if not econ_recruit_first[a]:
                r += 12.0
                econ_recruit_first[a] = True
                print(f"[ECON] first RECRUIT tier={a-15} (act{a}) step {traj['steps']} +12", flush=True)
                # --- 优先级4 (后半): 资源→招兵 50步闭环 +15 / 局 ---
                if (not econ_closure_done) and econ_resource_step is not None:
                    if (traj["steps"] - econ_resource_step) <= 50:
                        r += 15.0
                        econ_closure_done = True
                        print(f"[ECON] closure (resource→recruit {traj['steps']-econ_resource_step}s) step {traj['steps']} +15", flush=True)
            elif _rc_rewarded:
                print(f"[ECON] recruit tier={a-15} (act{a}) step {traj['steps']} +0.5", flush=True)
        # --- 优先级2: BUILD_2 (兵种建筑, 动作20) first +15 + 每次执行小额 (撤梯子② 3→1.5; ③-S1 1.5→0.75) ---
        if a == 20:
            econ_build2_count += 1
            _b2_rewarded = econ_build2_count <= 5
            if _b2_rewarded:
                r += 0.75
            if not econ_build2_done:
                r += 15.0
                econ_build2_done = True
                print(f"[ECON] first BUILD_2 (creature dwelling, act20) step {traj['steps']} +15", flush=True)
            elif _b2_rewarded:
                print(f"[ECON] build2 (act20) step {traj['steps']} +0.75", flush=True)
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
