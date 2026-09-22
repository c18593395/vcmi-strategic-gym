#!/usr/bin/env python3
"""WSL2 PPO v2 — GAE λ=0.90 + 梯度裁剪 1.0 — 多步自对弈训练 (GPU)"""
import subprocess, json, time, os, random, signal, sys, shutil, math
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

# === C4.2: 扩规模 ===
# 2026-08-29 Level 3 晋级 (II.2 切 T04, 不开经济): BATCH 1024→2048 / EPOCHS 4→6 / EXTREME_ADV_CLIP 5.0→6.0
N_EPISODES, BATCH, STEPS_PER_EP = 1000, 2048, 250
LR, CLIP, EPOCHS = 3e-4, 0.2, 6
GAMMA, GAE_LAMBDA = 0.99, 0.90
GRAD_CLIP_MAX = 1.0
EXTREME_ADV_CLIP = 6.0
# === P5/D3: 开局熵 bonus (B3 方案 docs/方案_B1-B4_20260829.md) ===
# 训练侧 ent_coef 前期x2, 按全局步数指数衰减; 治开局动作熵~0 (换图/对手池无适应力)
# 不动 ep_runner = 无环境奖励污染; 衰减钟锚 total_steps, checkpoint resume 自动延续
ENT_COEF_BASE = 0.05
ENT_WARMUP_STEPS = 2_000_000
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
# 09-06 再移除 36X36_02: 守卫减半后 51 局仍全部负分 (-50→-181 恶化趋势) — 非守卫兵量问题, 疑守卫位置/地形结构压制红方路线; 两次移出, 回归需重设计该图
MAPS = [
    # 09-13 减 T05 MIR 3 张（去 36X36_01_mir / 52X52_01_mir / 52X52_02_mir），加 T04 2 张（36X36_01 + 30X30_01）
    # 目的：T05 难度上移 + T04 死路密集为 T7.4 判据 1（ZOMBIE 样本）提供触发条件
    # T04 已退役存档 09-04，但 T7.4 方向纠正后确认"高障碍图"是判据 1 唯一样本源
    "T05_adventure_36X36_01.vmap",
    "T05_adventure_52X52_01.vmap",
    "T05_adventure_52X52_02.vmap",
    # 09-06 T06 前置 (方案 A, 只加大图轴不加多敌轴): 72X72 1v1 duel 变体 (fix_t06_maps.py 去 hero_2/3+town_2/3)
    # identifier 三类修复同 T05 套路 (inham→edric/iona/alchemist / resourceGold→gold / monster→三兽集), inspect 5 图全绿
    # 09-06 晚 1v3 上线 (判据 4/4 达标: 32 局 后1/3 avg 83.0 vs 前1/3 65.1 比值 1.27 上行 / 自发 100% / 200步局 0% / 守卫胜 96.9%):
    # 混入 72X72_01 原版 (1 red vs 3 blue 英雄+3 蓝城, 只加多敌轴), MAPS 7→8
    # 回退线: avg_r 跌幅>30% (vs duel 基线 75.5) 或挂死局>40% → 移除回 7 图
    "T06_adventure_72X72_01_duel.vmap",
    "T06_adventure_72X72_01.vmap",
    # 09-12 capture 观察窗五判据全达标 (66 局 avg_r 180.2 / TOWN_BLOCKED 0 / TOWN_CAPTURE 24)
    # 错窗切地图轴: 加 72X72_02_duel (MAPS 9→10, 一次一轴)
    # 09-14 修复回池: 根因=header 缺 8 字段 (5→13, patch_t06_02_header_0914.py) + 运行时副本旧文件;
    #               完整局验过 95步/389s/r=130.7 rc0 零致命错误
    "T06_adventure_72X72_02_duel.vmap",
    # 09-13 H3M 官方图适配: King of Pain (SoD, 72X72, 3p, has_underground=0, 无船无水下)
    # py/vcmi_full_to_slim.py 转换: 1657→173 对象 (hero_0 + town_5 + mine_38 + resource_68 + monster_61)
    # 地形 gr57_ 系列 (gr24_ 变体), 无 rc/wa 前缀 → passable_grid 全通 (单层无桥无船一致)
    # 文件名加 _h3m 后缀 (strategic_env.py 强制要求 mapname 含 s1/mini/adventure/h3m)
    "King_of_Pain_h3m.vmap",
    # 09-13 地图轴扩展: T04 2 张移除, 加 T06 3 张 (72X72_02 / 108X108_02_duel / 108X108_02)
    # 09-14 修复回池: 同 header 缺字段根因 (patch_t06_02_header_0914.py, 13字段 + 双副本部署);
    #   完整局: 72_02 110步/432s/r=217.0, 108_02 93步/400s/r=416.4, 108_02_duel 30步/328s/r=36.2, 均 rc0 零致命错误
    "T06_adventure_72X72_02.vmap",
    "T06_adventure_108X108_02_duel.vmap",
    "T06_adventure_108X108_02.vmap",
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
RUNNER = "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py"
MODEL_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt"
STATE_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model_state.pt"
CLEAN_CKPT_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt"
# C2 L0: 崩溃局 ep_log 归档目录 (09-15)
CRASHLOG_DIR = "/mnt/d/Bigdata/hero3_fresh/crashlog"

# WIN-1 击杀激励批次A/B (09-16, 方案 docs/方案_WIN1_击杀激励重设计_20260916.md):
# ep_runner 新参数经环境变量注入 — 启动脚本 restart_train_v5_win1_batchA.sh 在 unit Environment= 注入;
# 默认未设 = 关闭零行为变化; 回退 = 原版 restart_train_v5_sys.sh (无注入)。duel 图由 runner 内部排除。
WIN1_ENV_ARGS = {
    "HOMM3_BLUE_HERO_GRAD": "--blue_hero_grad",           # P-H1 接近梯度 (批次A, 建议 0.2)
    "HOMM3_BLUE_HERO_GRAD_CAP": "--blue_hero_grad_cap",   # P-H1 每局上限 (批次A, 建议 25)
    "HOMM3_BLUE_HERO_CONTACT_R": "--blue_hero_contact_r", # P-H2 接战奖 (批次B, 建议 15)
    "HOMM3_BLUE_HERO_CONTACT_D": "--blue_hero_contact_d", # P-H2 判定距离阈值 (09-17 A2 修复, 批次B 建议 2=8邻;
                                                          # 0=旧行为仅同格, 而 d==0 结构性不可达 → 批次B 必须注入 2)
    "HOMM3_KILL_R_FIRST": "--kill_r_first",               # P-H3 首杀 (批次B, 建议 40)
    "HOMM3_KILL_R_NEXT": "--kill_r_next",                 # P-H3 后续杀 (批次B, 建议 30)
    "HOMM3_OWN_TOWN_DECAY": "--own_town_decay",           # A3 own_town 访问衰减 (09-17 同窗, 建议 0.5; 0=关)
    "HOMM3_OWN_TOWN_MAX_VISITS": "--own_town_max_visits", # A3 访问硬上限 (备用闸门, 0=不限)
    "HOMM3_BLUE_HERO_ATTACK_BYPASS": "--blue_hero_attack_bypass", # A2 攻击步旁路总开关 (09-17, 默认 0=关; 1=启用)
    "HOMM3_ATTACK_F_MIN": "--attack_f_min",               # A2 战力 logistic F 阈值 (09-17, 默认 0.0; 打不过不进入)
}
_win1_active = {k: os.environ[k] for k in WIN1_ENV_ARGS
                if os.environ.get(k) not in (None, "", "0", "0.0")}
if _win1_active:
    print("[WIN1_BATCH] env-injected runner args: "
          + " ".join(f"{WIN1_ENV_ARGS[k]}={v}" for k, v in sorted(_win1_active.items())), flush=True)


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

# === #293: 入池图蓝方 AI 标签 (h3m_batch_pipeline 写 _pool_index.json, 此处读) ===
# === WIN-5: H3M 池混合采样开关 (09-21 就绪默认关) — HOMM3_H3M_MIX=0.3 → 30% 局采 h3m_pool ===
# 错窗纪律: T7.8 观测窗内保持 0 (纯课程图), 观测窗收口后下一窗设 0.2-0.3 开混合轴
# === 入池批次过滤 (09-21): HOMM3_H3M_BATCH=1 → 只采 _pool_index.json 里
#    "batch" <= 1 的图（首批安全5张）。防负数核心: 设了 BATCH 时, 没标 batch
#    字段的图一律不放行（水/岛/地下图未标记 = 不入采样），只有显式标 batch 才入。
_POOL_INDEX_PATH = "/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/_pool_index.json"
_POOL_DIR = "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool"
_H3M_MIX = float(os.environ.get("HOMM3_H3M_MIX", "0"))
_H3M_BATCH = int(os.environ.get("HOMM3_H3M_BATCH", "0"))  # 0=不过滤, 1=只采有batch且<=1的图
_POOL_BLUE_AI = {}
_POOL_MAPS = []  # 池内实际存在且非 skip 的图 (混合采样候选)
_POOL_IDX_AT = 0.0


def _refresh_pool_blue_ai(force=False):
    global _POOL_BLUE_AI, _POOL_MAPS, _POOL_IDX_AT
    if not force and time.time() - _POOL_IDX_AT < 600:
        return
    try:
        idx = json.load(open(_POOL_INDEX_PATH, encoding="utf-8"))
        _POOL_BLUE_AI = {k: (v or {}).get("blue_ai", "MMAI_RANDOM")
                         for k, v in idx.items()}
        if os.path.isdir(_POOL_DIR):
            _POOL_MAPS = [f for f in os.listdir(_POOL_DIR)
                          if f.endswith(".vmap")
                          and _POOL_BLUE_AI.get(f) != "skip"
                          # 批次过滤: _H3M_BATCH=0 不过滤; >0 时只采显式标了 batch 且 <=阈值 的图
                          # (没标 batch 字段的水/岛/地下图一律放行, 防未学能力直接负数)
                          and (_H3M_BATCH == 0
                               or (idx.get(f, {}) or {}).get("batch") is not None
                               and (idx.get(f, {}) or {}).get("batch") <= _H3M_BATCH)]
    except Exception:
        pass  # 索引缺失/损坏 = 全部默认 MMAI_RANDOM + 不混池, 零行为变化
    _POOL_IDX_AT = time.time()


def run_episode(mapname, blue_model=None, blue_ai="MMAI_RANDOM"):
    """Run one episode using current model policy (not random).
    Saves model to temp file, spawns isolated subprocess."""
    # 09-14 防残留污染 (4 张新图 segfault 秒退实证): 开局先删上一局 traj,
    # 子进程若在首步写入前崩溃 → 文件不存在 → 下方读取抛错 return None, 杜绝旧轨迹被当新局
    if os.path.exists(EP_TRAJ):
        os.remove(EP_TRAJ)
    # Save current model to temp checkpoint for the subprocess
    ep_ckpt = f"/tmp/hermes_ep_model_{os.getpid()}.pt"
    torch.save(model.state_dict(), ep_ckpt)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    cmd = [VENV, RUNNER, str(STEPS_PER_EP), EP_TRAJ, mapname, "--model", ep_ckpt]
    # C8.5: blue 对手 — MMAI_RANDOM 自动随机行动 (NK2 内存爆炸 3.7-7.5GB/局 → WSL OOM, 已弃用)
    cmd.extend(["--blue_ai", blue_ai, "--blue_adventure_ai", "MMAI"])
    # A2 贴脸强攻 (09-17): bypass=1 开贴脸强攻总开关 + contact_d=2 八邻域贴脸判定
    # f_min (09-19 三修): -0.2 → 0.0 — 死局实录: pick F=-0.20 蓝英雄直奔被主动进攻战败 (10/10 同构),
    # -0.2 阈值卡边界全放行。F 真实化后正 F 才攻 (打有把握的仗), 负 F 先攒兵。
    cmd.extend(["--blue_hero_attack_bypass", "1", "--blue_hero_contact_d", "2", "--attack_f_min", "0.0"])
    # C8.5: 探索奖励 (新格子 +1)
    # ===== Level 3 II.3 开经济 (2026-08-29): explore 0.3 / economy_force 50 / nk2 0.45 三件套 =====
    # cmd.extend(["--reward_explore", "0.2"])  # 降探索奖励，减少信号冲突
    cmd.extend(["--reward_explore", "0.3"])  # Level 3 II.3: 经济动作初期需更多探索，避免 entropy 塌
    # MOVE_TO 引导 (2026-08-19 第5轮): bias 2.0 + 每局前 30 步强制 24, 前 200 ep 线性衰减
    # 第4轮教训: bias(+2.0) 对 BC 从未见过的码无效 (logit 极负, 55ep 24 零出现) → 采样强制才有效
    move_scale = max(0.5, 1.0 - ep_count / 200)  # 2026-08-25: 下限 0.5 常驻 (原衰减到 0 → 模型失去目标驱动 → 乱逛/横跳/零战斗)
    cmd.extend(["--move_to_bias", str(2.0 * move_scale)])
    if mapname.startswith(("T04", "T05", "T06")):
        # 2026-08-29 T04: 目标远 (矿 dist 25~41, T03 守卫 d<=6), 强制期需覆盖奔矿闭环 → 60 步常驻
        # 09-03 T05 混入: 36X36/52X52 矿 dist 同量级, 与 T04 同款 60 步
        # 09-06 T06 duel 混入: 72X72 大图矿 dist 更远, 同款 60 步
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
    # T06 move_to_force: duel=60 (蓝英雄 plen=129<250 可达, P10 引导前60步走24), 非duel=250 (蓝城全程引导)
    # act_loop_from_step=60 与 duel move_to_force=60 同步; 非duel T06 250步局 step≥60 后惩罚生效
    # 非 T06 不设 (默认 0=跟随 move_to_force)
    if mapname.startswith('T06'):
        cmd.extend(["--act_loop_from_step", "60"])
    # 守卫击杀自动终局 (2026-08-29): +100 后 15 步内无新目标 → 提前结束 episode。
    # 治杀守卫后英雄存活长期振荡烧分 (每步-0.1+循环惩罚 → final r 跌破 80 晋级线, 20X20_01 全 0 胜)。
    # 新目标 (守卫/矿/资源) 自动重置倒计时; 回退 = 注释本行 (runner 默认 0=关闭)
    cmd.extend(["--guard_done_steps", "15"])
    # T04 目标引导 (2026-08-29): 首占矿/首进城镇各 +30 一次性事件 (T04 无守卫缺目标驱动源)。
    # 回退 = 注释本行 (runner 默认 0=关闭)
    cmd.extend(["--objective_reward", "30"])
    # WIN-1 批次A/B (09-16): 环境变量注入 ep_runner 激励参数 (模块头 WIN1_ENV_ARGS 映射);
    # 未设/0 = 不注入 → runner 默认 0 = 零行为变化; 值透传, duel 图由 runner 内部排除
    for _ek, _ea in WIN1_ENV_ARGS.items():
        if os.environ.get(_ek) not in (None, "", "0", "0.0"):
            cmd.extend([_ea, os.environ[_ek]])
    # Phase I.1: NK2 势函数奖励 (替代事件奖励)
    # ===== Level 3 II.3 开经济 (2026-08-29): scale 0.3→0.45 =====
    # cmd.extend(["--use_nk2_shaping", "--nk2_shaping_scale", "0.3"])  # 恢复NK2，scale=0.3 防critic爆炸
    cmd.extend(["--use_nk2_shaping", "--nk2_shaping_scale", "0.45"])  # Level 3: 经济长程行为需更强势函数引导
    # 随机军队 2026-08-26: 3000-5000 关闭 — 英雄太强 → 守卫 takenAction 评估 JOIN/FLEE (消失无战斗)
    # NK2 采集 (无 random_armies, swordsman 8) 守卫评估 FIGHT 战斗正常; 若英雄打不赢再另行加强守卫设计
    # cmd.extend(["--random_armies", "--random_army_min", "3000", "--random_army_max", "5000"])
    if blue_model:
        cmd.extend(["--blue_model", blue_model])
    # P10 target_list 加权排序 Python 旁路打分器 (09-15 灰度, 默认 legacy 零行为变化; scorer 启用 target_scorer.py 统一打分器)
    cmd.extend(["--target_chain", "scorer"])
    ep_log = f"/tmp/hermes_ep_{os.getpid()}.log"
    # === #296 日志降噪 (2026-09-23, 方案A): Popen 层 shell 管道过滤 ===
    # 根因: lib/callback/CCallback.cpp:53 sendQueryReply 收到 QueryID(-1) 时 logGlobal->error
    #       经 C++ std::cerr 直写 (踩坑 #296 勘误: 实际在 lib 非 mlclient; 铁律不重编 libvcmi.so)。
    # 现象: VCMI 引擎线程 (TBB worker N / runNetwork) 每 ~1.5s 一行刷屏, 无连锁报错 (Can not
    #       end turn / fishy / Disaster / THREW 全 0), 训练链路不受影响 (主日志 EP_TIME 全 err=no)。
    # 方案A: 不重编 C++, 在 Popen 层用 shell 管道 grep -v 按行过滤 C++ cerr 写入 hermes 日志的
    #       内容 (C++ std::cerr 不经过 Python sys.stdout, 只能 shell 管道层过滤)。
    #       扩展: 后续如发现其他刷屏良性噪声, 追加 grep -vE 模式 (正则或多次 -v)。
    # 回退: 把下面 3 行换回原 `proc = subprocess.Popen(cmd, stdout=open(ep_log,"w"),
    #       stderr=subprocess.STDOUT, env=env)` 即可 (2 行, 零其他改动)。
    _grep_filter = "grep -vE 'Cannot answer the query -1' || true"
    ep_log_fh = open(ep_log, "w")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
    )
    _grep_proc = subprocess.Popen(
        ["sh", "-c", _grep_filter],
        stdin=proc.stdout, stdout=ep_log_fh, stderr=subprocess.DEVNULL
    )
    proc.stdout.close()  # 父进程侧关闭 pipe 读端, 防 grep 写后死锁
    try: proc.wait(timeout=STEPS_PER_EP*60 + 300)  # C8.5: NK2 对手回合 15-60s, 原 *3+15 必误杀
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    ep_rc = proc.returncode  # 09-14: segfault/秒退非 0, 配合 traj 身份校验拦截残留污染
    # #296 降噪管道收尾: proc 已退出 → grep 的 stdin EOF → grep 自动结束; 显式 join 防残留
    try:
        _grep_proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _grep_proc.kill()
    ep_log_fh.close()  # 关闭 hermes 日志文件句柄 (grep 已 flush 完)
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
                # 09-10+: [EP_TIME] (局耗时打点 — 间歇性慢速 4-8s/步局 定量画像, 历史样本已丢失从此积累)
                # 09-15+: [SCORE] (P10 target_scorer 打分器每次 pick 诊断, 灰度观察 72_02 蓝英雄入池)
                # 09-16+: WIN-1 批次A/B 事件行 ([BHERO_GRAD] ep末接近梯度汇总 / [BHERO_SLAIN] 击杀阶梯 /
                #         [BHERO_CONTACT] 接战) — 否则批次A判据"距离 p50"无持久数据(实勘 17 局全被过滤)
                highlights = [l.rstrip("\n") for l in lines
                              if any(k in l for k in ("[ZOMBIE]", "[HERO_DEATH]", "[ENDTURN_FUSE]", "[ERROR]", "[GUARD]",
                                                      "[MINE]", "[TOWN",
                                                      "[START_HOME]", "[RECRUITED]",
                                                      "[EP_TIME]",
                                                      "[SCORE]",
                                                      "[ECON]",
                                                      "[EP298_SWALLOW]", "adventure_wait timed out",
                                                      "[BHERO_GRAD]", "[BHERO_SLAIN]", "[BHERO_CONTACT]",
                                                      "[BHERO_ATTACK]", "[BHERO_KILL]", "[ATK_DBG]",
                                                      "Assertion",
                                                      "end ep at step", "fuse-break",
                                                      "cycle_detect triggered", "penalty END_TURN",
                                                      "Segmentation fault", "core dumped",
                                                      "Disaster happened", "terminate called",
                                                      "AddressSanitizer"))]
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
        # 09-14 三道拦截: 子进程崩溃(rc!=0) / traj 是上一局残留(身份不符) / obs 全零 → 一律 return None 不入 buffer
        if ep_rc != 0:
            # C2 L0: rc 信号名翻译 (09-15)
            _sig_map = {-(int(v)): v for v in dir(signal) if v.startswith("SIG") if isinstance(getattr(signal, v), int)}
            _sig_name = _sig_map.get(ep_rc, f"rc={ep_rc}")
            # C2 L0: 崩溃局 ep_log 归档不覆盖 (09-15)
            try:
                os.makedirs(CRASHLOG_DIR, exist_ok=True)
                _ts = int(time.time())
                _crash_dest = os.path.join(CRASHLOG_DIR, f"ep_{mapname}_{resume_step:07d}_{_ts}.log")
                if os.path.exists(ep_log):
                    shutil.copy2(ep_log, _crash_dest)
                print(f"  [FILTER] ep 子进程非正常退出 {_sig_name}, 已归档 crashlog/{os.path.basename(_crash_dest)}, 丢弃防残留污染 map={mapname}", flush=True)
            except Exception:
                print(f"  [FILTER] ep 子进程非正常退出 {_sig_name}, 丢弃防残留污染 map={mapname}", flush=True)
            return None
        if d.get("mapname") != mapname:
            print(f"  [FILTER] traj 身份不符 traj_map={d.get('mapname')} != 调度={mapname}, 丢弃防残留污染", flush=True)
            return None
        if d.get("steps",0)>0 and not d.get("error"):
            if "obs" in d and len(d["obs"]) > 0 and len(d["obs"][0]) > 30:
                obs_nz = np.count_nonzero(d["obs"][0])
                acts = d.get("act", [])
                print(f"  ep_steps={d.get('steps',0)} r={d.get('total_rew',0):.2f} act={acts} obs_nz={obs_nz} map={mapname}", flush=True)
                # 2026-09-13 方案 A: 全零 obs 局 (引擎 reset 冷启动竞态, obs_nz=0) 不进 buffer —
                # 02_duel 4 局 steps=1 secs=603 实证: 首拍 obs 全零 + 无效动作 = 脏样本污染 PPO 价值网
                if obs_nz == 0:
                    print(f"  [FILTER] obs_nz=0 脏样本丢弃 (引擎 reset 竞态), 不进 buffer map={mapname}", flush=True)
                    return None
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

    _refresh_pool_blue_ai()  # #293: 10min 缓存刷新蓝方 AI 标签 + WIN-5 池图列表
    if _H3M_MIX > 0 and _POOL_MAPS and random.random() < _H3M_MIX:
        # WIN-5 混合轴: 按比例采 h3m_pool (默认 0=纯课程图, 观测窗内不动)
        _map = random.choice(_POOL_MAPS)
    else:
        _map = random.choice(MAPS)
    _blue_ai = _POOL_BLUE_AI.get(_map, "MMAI_RANDOM")
    traj = run_episode(_map, blue_model=blue_model, blue_ai=_blue_ai)
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
        ent_coef_t, ent_mean = ENT_COEF_BASE, 0.0  # P5/D3: 熵调度循环外初值
        for _ in range(EPOCHS):
            pi, val = model(obs_t, terrain_t)
            logp = pi.log_prob(act_t)
            ratio = (logp - logp_old).exp()
            # 额外钳位：阻止 ratio 爆炸产生 inf
            ratio = ratio.clamp(max=100.0)
            surr = -torch.min(ratio*adv, torch.clamp(ratio,1-CLIP,1+CLIP)*adv).mean()
            # v2: value loss against GAE returns instead of TD target
            vloss = nn.MSELoss()(val, returns.detach())
            # P5/D3: 熵系数 x(1+exp(-step/2M)): 0步->0.10(x2) / 200万->0.068 / 400万->0.057 / inf->0.05
            ent_coef_t = ENT_COEF_BASE * (1.0 + math.exp(-total_steps / ENT_WARMUP_STEPS))
            ent_mean = pi.entropy().mean()
            loss = surr + 0.5*vloss - ent_coef_t * ent_mean
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
        print(f"  step{total_steps:>5d} avg_r={rew_t.mean():.1f} vloss={vloss.item():.3f} loss={loss.item():.3f}{kl_str} ep={ep_count} time={elapsed:.0f}s entc={ent_coef_t:.4f} ent={ent_mean.item():.3f}", flush=True)

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
