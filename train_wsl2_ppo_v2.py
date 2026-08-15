#!/usr/bin/env python3
"""WSL2 PPO v2 — GAE λ=0.90 + 梯度裁剪 1.0 — 多步自对弈训练 (GPU)"""
import subprocess, json, time, os, random, signal, sys
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

# === C4.2: 扩规模 ===
N_EPISODES, BATCH, STEPS_PER_EP = 1000, 128, 200
LR, CLIP, EPOCHS = 5e-5, 0.2, 4
GAMMA, GAE_LAMBDA = 0.99, 0.90
GRAD_CLIP_MAX = 1.0
EXTREME_ADV_CLIP = 10.0
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === C3.2: 对手池 ===
OPPONENT_POOL_SIZE = 10

# === C8.5: MAPS — 2 人图 (blue=Nullkiller2 真对手, 无 tan 拖慢) ===
MAPS = [
    "Dungeon Keeper.h3m", "Key to Victory.h3m",
    "Good Witch, Bad Witch.h3m", "Fort Noxis.h3m",
]

# === A+B: KL 约束 BC — 防止 PPO 微调偏离 BC 专家行为 (参考策略 = 冻结的 bc_model) ===
KL_COEF = 0.05
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
        self.fc = nn.Sequential(nn.Linear(3464,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor, self.critic = nn.Linear(128,25), nn.Linear(128,1)
    def forward(self, x):
        h = self.fc(x)
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
    cmd.extend(["--reward_explore", "1.0"])
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
        with open(EP_TRAJ) as f: d = json.load(f)
        if d.get("steps",0)>0 and not d.get("error"):
            if "obs" in d and len(d["obs"]) > 0 and len(d["obs"][0]) > 30:
                obs_nz = np.count_nonzero(d["obs"][0])
                acts = d.get("act", [])
                print(f"  ep_steps={d.get('steps',0)} r={d.get('total_rew',0):.2f} act={acts} obs_nz={obs_nz}", flush=True)
            return d
    except: pass
    return None


model = Net().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=LR)
# C8.5: BC 权重路径 — 存在则优先于旧 MODEL_PATH 初始化 (fc+actor 有 NK2 行为知识)
BC_PATH = "/mnt/d/Bigdata/hero3_fresh/bc_model_v3464.pt"
# 尝试加载已有模型续训（优先完整状态，含优化器）
resume_step = 0
bc_loaded = False  # 无条件初始化: resume 路径跳过下方 BC 块时 line 121 不再 NameError
if os.path.exists(STATE_PATH):
    try:
        sd = torch.load(STATE_PATH, map_location=DEVICE, weights_only=False)
        model.load_state_dict(sd["model"])
        opt.load_state_dict(sd["optimizer"])
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
            model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
            print("Loaded existing model (weights only), continuing training", flush=True)
        except: pass

# === A+B: KL 约束 BC — 冻结 BC 参考网络, PPO 更新时对策略分布加 KL 正则 ===
USE_KL = False
kl_ref = None
# resume 路径 (resume_step>0) 同样重建 kl_ref: KL 约束不能因断点续训而丢失
if bc_loaded or resume_step > 0:
    try:
        kl_ref = Net().to(DEVICE)
        # 加载完整 BC 权重 (fc+actor+critic); 只取 actor 分布做 KL, critic 无影响
        kl_ref.load_state_dict(torch.load(BC_PATH, map_location=DEVICE, weights_only=True), strict=False)
        kl_ref.requires_grad_(False)  # 冻结: 不进优化器, 不参与反向传播
        kl_ref.eval()
        USE_KL = True
        print(f"  KL constraint ON: KL_COEF={KL_COEF}, kl_ref frozen from BC (fc+actor)", flush=True)
    except Exception as e:
        USE_KL = False
        kl_ref = None
        print(f"  KL constraint OFF (ref load failed: {e}) — 从零训练不约束", flush=True)
else:
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
                    model.load_state_dict(sd["model"])
                else:
                    model.load_state_dict(sd)
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
                model.load_state_dict(sd["model"])
            else:
                model.load_state_dict(sd)
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

buffer = {"obs":[],"act":[],"rew":[],"nobs":[],"done":[]}
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
        nobs_t = torch.tensor(np.array(buffer["nobs"][:BATCH]), dtype=torch.float32, device=DEVICE)
        done_t = torch.tensor(buffer["done"][:BATCH], dtype=torch.float32, device=DEVICE)

        with torch.no_grad():
            pi_old, val_old = model(obs_t)       # V(s)
            logp_old = pi_old.log_prob(act_t)
            _, val_next = model(nobs_t)          # V(s')

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
        # GAE returns for value targets
        returns = (gaes + val_old).clamp(-EXTREME_ADV_CLIP * 3, EXTREME_ADV_CLIP * 3)

        kl_item = 0.0  # A+B: KL 日志 (USE_KL 关闭时恒为 0)
        for _ in range(EPOCHS):
            pi, val = model(obs_t)
            logp = pi.log_prob(act_t)
            ratio = (logp - logp_old).exp()
            # 额外钳位：阻止 ratio 爆炸产生 inf
            ratio = ratio.clamp(max=100.0)
            surr = -torch.min(ratio*adv, torch.clamp(ratio,1-CLIP,1+CLIP)*adv).mean()
            # v2: value loss against GAE returns instead of TD target
            vloss = nn.MSELoss()(val, returns.detach())
            loss = surr + 0.5*vloss - 0.01*pi.entropy().mean()
            # === A+B: KL 约束 BC — 当前策略分布 vs 冻结的 BC 参考策略 ===
            # kl = Σ_a π(a) * (log π(a) - log π_ref(a)); kl_ref 前向在 no_grad 下
            if USE_KL:
                with torch.no_grad():
                    ref_pi, _ = kl_ref(obs_t)
                    ref_logp = ref_pi.logits.log_softmax(-1)
                cur_logp = pi.logits.log_softmax(-1)
                kl = (pi.probs * (cur_logp - ref_logp)).sum(-1).mean()
                loss = loss + KL_COEF * kl
                kl_item = kl.item()
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
        kl_str = f" kl={kl_item:.3f}" if USE_KL else ""
        print(f"  step{total_steps:>5d} avg_r={rew_t.mean():.1f} vloss={vloss.item():.0f} loss={loss.item():.0f}{kl_str} ep={ep_count} time={elapsed:.0f}s", flush=True)

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
print(f"\nDONE: {ep_count}eps {total_steps}steps {elapsed:.0f}s best_vloss={best_vloss:.0f}", flush=True)
torch.save(model.state_dict(), MODEL_PATH)
