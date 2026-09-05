#!/usr/bin/env python3
"""WSL2 PPO v2 — GAE λ=0.90 + 梯度裁剪 1.0 — 多步自对弈训练 (GPU)"""
import subprocess, json, time, os, random, signal, sys
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

# === C4.2: 扩规模 ===
# 2026-08-29 Level 3 晋级 (II.2 切 T04, 不开经济): BATCH 1024→2048 / EPOCHS 4→6 / EXTREME_ADV_CLIP 5.0→6.0
N_EPISODES, BATCH, STEPS_PER_EP = 1000, 2048, 200
LR, CLIP, EPOCHS = 3e-4, 0.2, 6
GAMMA, GAE_LAMBDA = 0.99, 0.90
GRAD_CLIP_MAX = 1.0
EXTREME_ADV_CLIP = 6.0
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ===== Level 3 (T04) 晋级+开经济时启用：取消下方 5 行注释，同时注释掉上方对应原值 =====
# BATCH = 2048             # 动作空间从 8(方向)+24(MOVE_TO) 扩到 14(+6内政)，样本需求 ×2 — 已启用 (08-29 晋级)
# EPOCHS = 6               # 内政奖励 r 量级(+5/+8/+15)与探索(+0.2)差异大，多 2 epoch 让 critic 拟合 — 已启用 (08-29 晋级)
# EXTREME_ADV_CLIP = 6.0   # BATCH 加大后，极端优势 clip 阈值略上调 (防经济首胜+100+15叠加削平) — 已启用 (08-29 晋级)
# (NK2 0.45 / EXPLORE 0.3 切换注释在 run_episode 函数内 L106/L91 处)
# ===== END Level 3 超参切换块 =====

# === C3.2: 对手池 ===
OPPONENT_POOL_SIZE = 10

# === 2026-08-29 Level 3 晋级 (II.2): T04 六图, 经济动作 16-21 仍关 (开经济 = 第二阶段, 一次一轴) ===
# T03 毕业战绩: eval 10/10 全胜 avg_r=99 / 最近100局首胜率 64% / 30X30_01 A/B 44局 0% 大负率
# ===== T04 课程 (退役存档 09-04, 如需回退换回) =====
# MAPS = [
#     "T04_adventure_20X20_01.vmap",
#     "T04_adventure_20X20_02.vmap",
#     "T04_adventure_30X30_01.vmap",
#     "T04_adventure_30X30_02.vmap",
#     "T04_adventure_36X36_01.vmap",
#     "T04_adventure_36X36_02.vmap",
#     # 09-03 加图 (观察窗触发条件①: 96ep 自发经济仍 0 + 固化依旧): 180° 旋转变体, 0 守卫同级同特征
#     "T04_adventure_20X20_03_mir.vmap",
#     "T04_adventure_20X20_04_mir.vmap",
#     "T04_adventure_30X30_03_mir.vmap",
#     "T04_adventure_30X30_04_mir.vmap",
#     "T04_adventure_36X36_03_mir.vmap",
#     "T04_adventure_36X36_04_mir.vmap",
# ]
# === 09-04 T05 全面化 (方案 B, 用户拍板): 判据实质达标 (T05 三图高分剧本近乎全胜 32/34 局 + 自发经济 0→54 次/40ep + 200 步局 24.4% 无大负局) → 全切 T05 三图 ===
# T04 12 图退役存档 (原版 6 + _mir 6): T04 剧本 15-48 分已被 T05 战斗剧本 130-143 全面超越
# 09-05 扩图: +3 镜像变体 (gen_t05_expand.py, 守卫同步旋转难度不变) + 36X36_02 守卫减半回归 (swordsman8→4/archer10→5/peasant15→8 可赢难度) = 3→7 张
MAPS = [
    "T05_adventure_36X36_01.vmap",
    "T05_adventure_36X36_02.vmap",
    "T05_adventure_52X52_01.vmap",
    "T05_adventure_52X52_02.vmap",
    "T05_adventure_36X36_01_mir.vmap",
    "T05_adventure_52X52_01_mir.vmap",
    "T05_adventure_52X52_02_mir.vmap",
]
# ===== T03 课程 (毕业存档, 如需回退换回) =====
# MAPS = [
#     "T03_adventure_20X20_01.vmap",
#     "T03_adventure_20X20_02.vmap",
#     "T03_adventure_30X30_01.vmap",
# ]

# === A+B: KL 约束 BC — 防止 PPO 微调偏离 BC 专家行为 (参考策略 = 冻结的 bc_model) ===
# 2026-08-19 第5轮: 0.05 → 0.3 — 第4轮 kl 失控 (ep52 kl=7.4), 0.05 完全挡不住 BC 漂移
# 2026-08-19 第6轮: 固定 → 自适应 — 实际 kl 0.6~1.2 远超目标 0.1, 固定系数约束力不足
# 第6轮 v2: KL_TARGET 0.1→0.3, KL_COEF_MAX 5→10 — klc 瞬间触顶 5.0 仍压不住 kl
# 第7轮: KL_TARGET 0.3→0.4 (放宽约束), CLIP 0.1→0.08 (收紧更新步幅)
KL_TARGET = 0.50       # Phase I.2 v2: 0.15->0.30->0.50, 放宽KL约束让策略能离开BC
KL_COEF_INIT = 0.3     # 初始系数
KL_ADAPT_UP = 1.5      # KL 超目标 1.5× 时收紧
KL_ADAPT_DOWN = 0.7    # KL 低于目标 /1.5 时放松
KL_COEF_MIN = 0.05     # 提高底线: 给KL一定约束防止乱飞
KL_COEF_MAX = 10.0     # 上限 5→10, 给更强约束空间
maps_json_path = "/mnt/d/Bigdata/hero3_fresh/available_maps.json"
# Not loading from JSON — using verified-open maps only

VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
MODEL_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt"
STATE_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model_state.pt"
CLEAN_CKPT_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt"


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        # Obs branch (existing)
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


EP_TRAJ = "/tmp/traj_ep.json"  # per-episode trajectory file

def run_episode(mapname, blue_model=None):
    """Run one episode using current model policy (not random).
    Saves model to temp file, spawns isolated subprocess."""
    # Save current model to temp checkpoint for the subprocess
    ep_ckpt = f"/tmp/hermes_ep_model_{os.getpid()}.pt"
    torch.save(model.state_dict(), ep_ckpt)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    cmd = [VENV, RUNNER, str(STEPS_PER_EP), EP_TRAJ, mapname, "--model", ep_ckpt]
    # C8.5: blue 对手 — MMAI_RANDOM 自动随机行动 (NK2 内存爆炸 3.7-7.5GB/局 → WSL OOM, 已弃用)
    cmd.extend(["--blue_ai", "MMAI_RANDOM", "--blue_adventure_ai", "MMAI"])
    # C8.5: 探索奖励 (新格子 +1)
    # ===== Level 3 II.3 开经济 (2026-08-29): explore 0.3 / economy_force 50 / nk2 0.45 三件套 =====
    # cmd.extend(["--reward_explore", "0.2"])  # 降探索奖励，减少信号冲突
    cmd.extend(["--reward_explore", "0.3"])  # Level 3 II.3: 经济动作初期需更多探索，避免 entropy 塌
    # MOVE_TO 引导 (2026-08-19 第5轮): bias 2.0 + 每局前 30 步强制 24, 前 200 ep 线性衰减
    # 第4轮教训: bias(+2.0) 对 BC 从未见过的码无效 (logit 极负, 55ep 24 零出现) → 采样强制才有效
    move_scale = max(0.5, 1.0 - ep_count / 200)  # 2026-08-25: 下限 0.5 常驻 (原衰减到 0 → 模型失去目标驱动 → 乱逛/横跳/零战斗)
    cmd.extend(["--move_to_bias", str(2.0 * move_scale)])
    if mapname.startswith(("T04", "T05")):
        # 2026-08-29 T04: 目标远 (矿 dist 25~41, T03 守卫 d<=6), 强制期需覆盖奔矿闭环 → 60 步常驻
        # 09-03 T05 混入: 36X36/52X52 矿 dist 同量级, 与 T04 同款 60 步
        # 09-03 晚 60→200 实验失败回滚 (09-04 复查): 200 版 13/32 挂死局 + r=-429 + a=2 占 34% 第一大
        # + TOWNSTALL 10.4/ep — 全程引导把英雄拖着撞墙 (obj_best 长局/新图频繁失效, 无目标 fallback
        # endTurn 遍地); 60 版对照 18ep avg_r 1.8 有 +131 局 — 回滚 60, 观察窗继续
        cmd.extend(["--move_to_force", "60"])
    else:
        cmd.extend(["--move_to_force", str(int(30 * move_scale))])  # 2026-08-25: 15→30 (最近目标几步即达, 15 步引导结束时还没走向矿/守卫)
    # ===== Level 3 II.3 开经济 (2026-08-29): 启用 (B2 方案定值 24 步, 50 步实测学费过重 -25 空转罚+延误奔矿, 08-29 改回) =====
    cmd.extend(["--economy_force", "24"])  # 前24步 16-21 轮换硬采样 (BC 无样本→logits极负→必须采样强制)
    # 状态级循环检测: 8 步窗口同一 (hero,pos) >=5 次 → -3 + 强制随机方向 (治 [8,8,6,2] 动作循环)
    cmd.extend(["--cycle_detect", "5"])
    # 第7轮: 动作级循环惩罚 — 连续 4 步重复 / 8 步两两交替 → -3 (治 [3,7,3,7]/[2,2,2,2] 死循环,
    # 状态级/横跳只抓位置往返, 抓不住推进型动作循环; 强制阶段不检测)
    # 第7轮 v2: 3.0→1.8 — 3.0 诱发 10 END_TURN 投机 (ROUND3 10 占比 6%→17.8% 全场第一)
    cmd.extend(["--act_loop_penalty", "1.0"])  # 降循环惩罚，减少负reward干扰
    # 守卫击杀自动终局 (2026-08-29): +100 后 15 步内无新目标 → 提前结束 episode。
    # 治杀守卫后英雄存活长期振荡烧分 (每步-0.1+循环惩罚 → final r 跌破 80 晋级线, 20X20_01 全 0 胜)。
    # 新目标 (守卫/矿/资源) 自动重置倒计时; 回退 = 注释本行 (runner 默认 0=关闭)
    cmd.extend(["--guard_done_steps", "15"])
    # T04 目标引导 (2026-08-29): 首占矿/首进城镇各 +30 一次性事件 (T04 无守卫缺目标驱动源)。
    # 回退 = 注释本行 (runner 默认 0=关闭)
    cmd.extend(["--objective_reward", "30"])
    # Phase I.1: NK2 势函数奖励 (替代事件奖励)
    # ===== Level 3 II.3 开经济 (2026-08-29): scale 0.3→0.45 =====
    # cmd.extend(["--use_nk2_shaping", "--nk2_shaping_scale", "0.3"])  # 恢复NK2，scale=0.3 防critic爆炸
    cmd.extend(["--use_nk2_shaping", "--nk2_shaping_scale", "0.45"])  # Level 3: 经济长程行为需更强势函数引导
    # 随机军队 2026-08-26: 3000-5000 关闭 — 英雄太强 → 守卫 takenAction 评估 JOIN/FLEE (消失无战斗)
    # NK2 采集 (无 random_armies, swordsman 8) 守卫评估 FIGHT 战斗正常; 若英雄打不赢再另行加强守卫设计
    # cmd.extend(["--random_armies", "--random_army_min", "3000", "--random_army_max", "5000"])
    if blue_model:
        cmd.extend(["--blue_model", blue_model])
    ep_log = f"/tmp/hermes_ep_{os.getpid()}.log"
    proc = subprocess.Popen(
        cmd,
        stdout=open(ep_log, "w"), stderr=subprocess.STDOUT, env=env
    )
    try: proc.wait(timeout=STEPS_PER_EP*60 + 300)  # C8.5: NK2 对手回合 15-60s, 原 *3+15 必误杀
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    try:
        # Clean up temp checkpoint
        if os.path.exists(ep_ckpt):
            os.remove(ep_ckpt)
        # === OPS-20260828-01: 把 ep_runner 的 stdout (含 [ZOMBIE] / [ENDTURN_FUSE]) 转储进主日志, 便于监控验收 d/e ===
        if os.path.exists(ep_log):
            try:
                with open(ep_log, "r", errors="replace") as f:
                    lines = f.readlines()
                # P4 (08-29): 词表补 [GUARD] (守卫首胜事件此前从不进主日志) + "Assertion" (引擎断言崩溃行不带 [ERROR] 方括号, 漏网)
                # 08-29+: [MINE]/[TOWN] (T04 目标引导首访事件)
                # 09-02+: [START_HOME]/[RECRUITED] (招兵四拍判据链 1/4 与 4/4 拍, ep 日志逐局覆盖防丢失)
                highlights = [l.rstrip("\n") for l in lines
                              if any(k in l for k in ("[ZOMBIE]", "[ENDTURN_FUSE]", "[ERROR]", "[GUARD]",
                                                      "[MINE]", "[TOWN",
                                                      "[START_HOME]", "[RECRUITED]",
                                                      "Assertion",
                                                      "end ep at step", "fuse-break",
                                                      "cycle_detect triggered", "penalty END_TURN"))]
                if highlights:
                    for l in highlights:
                        print(f"  {l}", flush=True)
                else:
                    tail3 = [l.rstrip("\n") for l in lines[-3:] if l.strip()]
                    for l in tail3:
                        if l.strip().startswith(("===", "Run", "Reward", "Error", "Obs")):
                            print(f"  {l}", flush=True)
            except Exception as ep_exc:
                print(f"  [WARN] ep_log dump failed: {ep_exc}", flush=True)
        with open(EP_TRAJ) as f: d = json.load(f)
        if d.get("steps",0)>0 and not d.get("error"):
            if "obs" in d and len(d["obs"]) > 0 and len(d["obs"][0]) > 30:
                obs_nz = np.count_nonzero(d["obs"][0])
                acts = d.get("act", [])
                print(f"  ep_steps={d.get('steps',0)} r={d.get('total_rew',0):.2f} act={acts} obs_nz={obs_nz} map={mapname}", flush=True)
            return d
    except: pass
    return None


model = Net().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=LR)
# C8.5: BC 权重路径 — 存在则优先于旧 MODEL_PATH 初始化 (fc+actor 有 NK2 行为知识)
# 2026-08-17 H.8: v3464b = 新采集 (All for One 34 局 28903 pairs, NK2 卡死修复后) 训练产物
BC_PATH = "/mnt/d/Bigdata/hero3_fresh/bc_model_v3464b.pt"
# 尝试加载已有模型续训（优先完整状态，含优化器）
resume_step = 0
bc_loaded = False  # 无条件初始化: resume 路径跳过下方 BC 块时 line 121 不再 NameError
if os.path.exists(STATE_PATH):
    try:
        sd = torch.load(STATE_PATH, map_location=DEVICE, weights_only=False)
        model.load_state_dict(sd["model"], strict=False)
        opt.load_state_dict(sd["optimizer"])  # Optimizer.load_state_dict 无 strict 参数 (TypeError → 永远 fallback BC)
        resume_step = sd.get("step", 0)
        print(f"Loaded train state (model+optimizer, step={resume_step})", flush=True)
    except:
        print("Failed to load STATE_PATH, falling back to MODEL_PATH", flush=True)
if resume_step == 0:
    bc_loaded = False
    if os.path.exists(BC_PATH):
        try:
            sd = torch.load(BC_PATH, map_location=DEVICE, weights_only=True)
            sd.pop("critic.weight", None); sd.pop("critic.bias", None)  # critic 保持随机, PPO 从头学
            model.load_state_dict(sd, strict=False)
            bc_loaded = True
            print("Loaded BC weights (fc+actor), critic random — C8.5 微调起点", flush=True)
        except Exception as e:
            print(f"BC load failed: {e}, fallback to MODEL_PATH", flush=True)
    if not bc_loaded and os.path.exists(MODEL_PATH):
        try:
            model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True, strict=False), strict=False)
            print("Loaded existing model (weights only), continuing training", flush=True)
        except: pass

# === A+B: KL 约束 BC — 冻结 BC 参考网络, PPO 更新时对策略分布加 KL 正则 ===
USE_KL = False
kl_ref = None
# resume 路径 (resume_step>0) 同样重建 kl_ref: KL 约束不能因断点续训而丢失
if bc_loaded or resume_step > 0:
    try:
        kl_ref = Net().to(DEVICE)  # shares same architecture
        # 加载完整 BC 权重 (fc+actor+critic); 只取 actor 分布做 KL, critic 无影响
        kl_ref.load_state_dict(torch.load(BC_PATH, map_location=DEVICE, weights_only=True), strict=False)
        kl_ref.requires_grad_(False)  # 冻结: 不进优化器, 不参与反向传播
        kl_ref.eval()
        USE_KL = True
        kl_coeff = KL_COEF_INIT
        print(f"  KL adaptive ON: target={KL_TARGET}, coef_init={kl_coeff}, kl_ref frozen from BC", flush=True)
    except Exception as e:
        USE_KL = False
        kl_ref = None
        kl_coeff = 0.0
        print(f"  KL constraint OFF (ref load failed: {e}) — 从零训练不约束", flush=True)
else:
    kl_coeff = 0.0
    print(f"  KL constraint OFF (no BC base loaded) — 从零训练不约束", flush=True)

def is_clean():
    for p in model.parameters():
        if torch.isnan(p).any() or torch.isinf(p).any():
            return False
    return True

def save_train_state(path, step=0):
    torch.save({"model": model.state_dict(), "optimizer": opt.state_dict(), "step": step}, path)

def restore_clean():
    global opt, warmup_until_load, warmup_batches
    warmup_until_load = True
    warmup_batches = 0
    ckpt_dir = "/mnt/d/Bigdata/hero3_fresh/checkpoints"
    # 先试黑名单指定 snapshot
    for fallback in [CLEAN_CKPT_PATH]:
        if os.path.exists(fallback):
            try:
                sd = torch.load(fallback, map_location=DEVICE, weights_only=False)
                if "model" in sd:
                    model.load_state_dict(sd["model"], strict=False)
                else:
                    model.load_state_dict(sd, strict=False)
                if is_clean():
                    print(f"  Restored clean checkpoint from blacklist: {os.path.basename(fallback)}", flush=True)
                    opt = torch.optim.Adam(model.parameters(), lr=LR)
                    return
            except: pass
    ckpts = sorted([f for f in os.listdir(ckpt_dir) if f.startswith("wsl2_ckpt_") and f.endswith(".pt")],
                   key=lambda f: int(f.replace("wsl2_ckpt_", "").replace(".pt", "")))
    for ckpt in reversed(ckpts):
        path = os.path.join(ckpt_dir, ckpt)
        try:
            sd = torch.load(path, map_location=DEVICE, weights_only=False)
            if "model" in sd:
                model.load_state_dict(sd["model"], strict=False)
            else:
                model.load_state_dict(sd, strict=False)
            if is_clean():
                print(f"  Restored clean checkpoint: {ckpt}", flush=True)
                opt = torch.optim.Adam(model.parameters(), lr=LR)
                return
        except: pass
    model.apply(lambda m: m.reset_parameters() if hasattr(m, 'reset_parameters') else None)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    print("  No clean checkpoint found, reinitialized model", flush=True)

def save_shutdown(*args):
    """SIGTERM/SIGINT 时保存当前状态，确保关机不丢进度"""
    print("\n  Shutdown signal received, saving current state...", flush=True)
    if is_clean():
        save_train_state(STATE_PATH, step=total_steps)
        torch.save(model.state_dict(), MODEL_PATH)
        print(f"  Saved STATE_PATH (step={total_steps}) and MODEL_PATH", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, save_shutdown)
signal.signal(signal.SIGINT, save_shutdown)

buffer = {"obs":[],"act":[],"rew":[],"nobs":[],"done":[],"terrain_grid":[]}
total_steps, ep_count, best_vloss, last_ckpt_step = resume_step, 0, float("inf"), resume_step

# === C3.2: 对手池初始化 ===
opponent_pool = []

print(f"WSL2 PPO v2 — {N_EPISODES}eps×{STEPS_PER_EP}steps batch={BATCH} maps={len(MAPS)} device={DEVICE}", flush=True)
print(f"  GAE λ={GAE_LAMBDA}  grad_clip={GRAD_CLIP_MAX}  gamma={GAMMA}", flush=True)
print(f"  自对弈: red=MMAI_USER blue=MMAI_USER/对手池", flush=True)
t0 = time.time()
# LR 预热：从 MODEL_PATH 加载（新鲜优化器）时前 5 batch 渐增 LR，防止 NaN
warmup_until_load = (resume_step == 0)
warmup_batches = 0
LR_TARGET = LR

for ep in range(N_EPISODES):
    # === C3.2: 选择对手 ===
    blue_model = None
    if opponent_pool:
        r = random.random()
        if r < 0.7:
            blue_model = None          # 当前模型
        elif r < 0.9:
            # 早期版本（池中前半部分）
            blue_model = random.choice(opponent_pool[:max(1, len(opponent_pool)//2)])
        else:
            blue_model = random.choice(opponent_pool)  # 随机旧版
    # 对手池为空时 blue_model 保持 None，用当前模型自对弈

    traj = run_episode(random.choice(MAPS), blue_model=blue_model)
    ep_count += 1
    if traj is None: continue
    for i in range(traj["steps"]):
        for k in ["obs","act","rew","nobs","done"]:
            buffer[k].append(traj[k][i])
        total_steps += 1

    # 每局一行日志
    ep_rew = np.mean(traj["rew"]) if traj["steps"] > 0 else 0.0
    print(f"  step{total_steps:>5d} avg_r={ep_rew:.1f} ep={ep_count} time={time.time()-t0:.0f}s", flush=True)

    if len(buffer["obs"]) >= BATCH:
        obs_t  = torch.tensor(np.array(buffer["obs"][:BATCH]), dtype=torch.float32, device=DEVICE)
        act_t  = torch.tensor(buffer["act"][:BATCH], dtype=torch.long, device=DEVICE)
        rew_t  = torch.tensor(buffer["rew"][:BATCH], dtype=torch.float32, device=DEVICE)
        rew_t  = rew_t.clamp(-5.0, 5.0)  # Phase I.2: clip extreme rewards
        nobs_t = torch.tensor(np.array(buffer["nobs"][:BATCH]), dtype=torch.float32, device=DEVICE)
        done_t = torch.tensor(buffer["done"][:BATCH], dtype=torch.float32, device=DEVICE)
        # Terrain grid tensor (B, 4, 21, 21)
        tg_list = buffer["terrain_grid"][:BATCH]
        if len(tg_list) == BATCH and len(tg_list[0]) > 0:
            terrain_t = torch.tensor(np.array(tg_list), dtype=torch.float32, device=DEVICE)
        else:
            terrain_t = None

        with torch.no_grad():
            pi_old, val_old = model(obs_t, terrain_t)       # V(s)
            logp_old = pi_old.log_prob(act_t)
            _, val_next = model(nobs_t, terrain_t)          # V(s')

        # === v2: GAE λ=0.95 ===
        # delta_t = r_t + γ * V(s_{t+1}) * (1-done_t) - V(s_t)
        # gae_t   = delta_t + (γ * λ) * (1-done_t) * gae_{t+1}
        deltas = rew_t + GAMMA * val_next * (1.0 - done_t) - val_old
        gaes = torch.zeros_like(deltas)
        gae = 0.0
        for t in reversed(range(len(deltas))):
            gae = deltas[t].item() + GAMMA * GAE_LAMBDA * (1.0 - done_t[t].item()) * gae
            gaes[t] = gae

        # 优势归一化
        adv = (gaes - gaes.mean()) / (gaes.std() + 1e-8)
        # 极端优势钳位，防止极值震荡
        adv = adv.clamp(-EXTREME_ADV_CLIP, EXTREME_ADV_CLIP)
        # GAE returns for value targets — 归一化防 critic 爆炸
        returns = gaes + val_old
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)

        kl_item = 0.0  # A+B: KL 日志 (USE_KL 关闭时恒为 0)
        for _ in range(EPOCHS):
            pi, val = model(obs_t, terrain_t)
            logp = pi.log_prob(act_t)
            ratio = (logp - logp_old).exp()
            # 额外钳位：阻止 ratio 爆炸产生 inf
            ratio = ratio.clamp(max=100.0)
            surr = -torch.min(ratio*adv, torch.clamp(ratio,1-CLIP,1+CLIP)*adv).mean()
            # v2: value loss against GAE returns instead of TD target
            vloss = nn.MSELoss()(val, returns.detach())
            loss = surr + 0.5*vloss - 0.05*pi.entropy().mean()
            # === A+B: KL 约束 BC — 当前策略分布 vs 冻结的 BC 参考策略 ===
            # kl = Σ_a π(a) * (log π(a) - log π_ref(a)); kl_ref 前向在 no_grad 下
            if USE_KL:
                with torch.no_grad():
                    ref_pi, _ = kl_ref(obs_t, terrain_t)
                    ref_logp = ref_pi.logits.log_softmax(-1)
                cur_logp = pi.logits.log_softmax(-1)
                kl = (pi.probs * (cur_logp - ref_logp)).sum(-1).mean()
                kl_loss = (kl_coeff * kl).clamp(max=10.0)  # clip KL contribution
                loss = loss + kl_loss
                kl_item = kl.item()
                # 自适应 KL: 根据实际 KL 值动态调节系数
                if kl_item > KL_TARGET * 1.5:
                    kl_coeff = min(kl_coeff * KL_ADAPT_UP, KL_COEF_MAX)
                elif kl_item < KL_TARGET / 1.5:
                    kl_coeff = max(kl_coeff * KL_ADAPT_DOWN, KL_COEF_MIN)
            opt.zero_grad()
            loss.backward()
            # NaN 梯度检测：一旦发现立即回退干净 checkpoint
            grad_ok = True
            for p in model.parameters():
                if p.grad is not None and (torch.isnan(p.grad).any() or torch.isinf(p.grad).any()):
                    grad_ok = False
                    break
            if not grad_ok:
                print(f"  NaN gradient at epoch {_}, restoring clean checkpoint...", flush=True)
                restore_clean()
                break
            # === v2: 梯度裁剪 ===
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP_MAX)
            # LR 预热：新鲜优化器前 5 batch 渐增 LR
            if warmup_until_load and warmup_batches < 5:
                warmup_scale = (warmup_batches + 1) / 5.0
                for pg in opt.param_groups:
                    pg["lr"] = LR_TARGET * warmup_scale
                warmup_batches += 1
                if warmup_batches >= 5:
                    for pg in opt.param_groups:
                        pg["lr"] = LR_TARGET
            opt.step()

        for k in buffer: buffer[k] = buffer[k][BATCH:]
        elapsed = time.time() - t0
        kl_str = f" kl={kl_item:.3f} klc={kl_coeff:.3f}" if USE_KL else ""
        print(f"  step{total_steps:>5d} avg_r={rew_t.mean():.1f} vloss={vloss.item():.3f} loss={loss.item():.3f}{kl_str} ep={ep_count} time={elapsed:.0f}s", flush=True)

        if vloss.item() < best_vloss:
            best_vloss = vloss.item()
            # 保存完整状态（模型+优化器+step）
            save_train_state(STATE_PATH, step=total_steps)
            # 同时保存模型权重（用于对手池/推理）
            torch.save(model.state_dict(), MODEL_PATH)

        # === checkpoint: 每 50 step 保存，保留最近 OPPONENT_POOL_SIZE 个 ===
        ckpt_dir = "/mnt/d/Bigdata/hero3_fresh/checkpoints"
        os.makedirs(ckpt_dir, exist_ok=True)
        if total_steps - last_ckpt_step >= 50:
            last_ckpt_step = total_steps
            ckpt_path = os.path.join(ckpt_dir, f"wsl2_ckpt_{total_steps}.pt")
            # 保存模型权重（不含优化器，保持兼容）
            torch.save(model.state_dict(), ckpt_path)
            # 每 50 step 同时保存完整状态（模型+优化器+step），保底重启不丢进度
            save_train_state(STATE_PATH, step=total_steps)

            # C3.2: 把新 checkpoint 加入对手池
            if ckpt_path not in opponent_pool:
                opponent_pool.append(ckpt_path)
            if len(opponent_pool) > OPPONENT_POOL_SIZE:
                opponent_pool.pop(0)

            # 保留最近 OPPONENT_POOL_SIZE 个文件，删除旧的
            ckpts = sorted(
                [f for f in os.listdir(ckpt_dir)
                 if f.startswith("wsl2_ckpt_") and f.endswith(".pt")],
                key=lambda f: int(f.replace("wsl2_ckpt_", "").replace(".pt", ""))
            )
            for f in ckpts[:-OPPONENT_POOL_SIZE]:
                os.remove(os.path.join(ckpt_dir, f))

elapsed = time.time() - t0
print(f"\nDONE: {ep_count}eps {total_steps}steps {elapsed:.0f}s best_vloss={best_vloss:.3f}", flush=True)
torch.save(model.state_dict(), MODEL_PATH)
