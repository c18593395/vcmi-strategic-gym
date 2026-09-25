#!/usr/bin/env python3
"""WSL2 PPO — 多步自对弈训练 (GPU) — C3.2+C4.2"""
import os
import subprocess, json, time, os, random, signal, sys
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

# === C4.2: 扩规模 ===
N_EPISODES, BATCH, STEPS_PER_EP = 1000, 128, 50
LR, CLIP, EPOCHS = 1e-4, 0.2, 4
GAMMA = 0.99
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === C3.2: 对手池 ===
OPPONENT_POOL_SIZE = 10

# === C4.2: MAPS 从 available_maps.json 加载，失败则 fallback ===
MAPS = [
    "Key to Victory.h3m", "Elbow Room.h3m", "Emerald Isles.h3m",
    "Golems Aplenty.h3m", "A Warm and Familiar Place.h3m",
    "All for One.h3m", "A Viking We Shall Go.h3m", "Dead and Buried.h3m",
]
maps_json_path = "/mnt/d/Bigdata/hero3_fresh/available_maps.json"
try:
    with open(maps_json_path) as f:
        loaded = json.load(f)
        if "maps" in loaded and len(loaded["maps"]) > 0:
            MAPS = loaded["maps"]
            print(f"Loaded {len(MAPS)} maps from available_maps.json", flush=True)
except Exception as e:
    print(f"Could not load available_maps.json ({e}), using hardcoded {len(MAPS)} maps", flush=True)

VENV = os.environ.get("VENV", "/home/administrator/vcmi-workspace/venv/bin/python")
RUNNER = os.environ.get("RUNNER", "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py")
TRAJ = "/tmp/traj_one.json"
MODEL_PATH = os.environ.get("MODEL_PATH", "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt")
STATE_PATH = os.environ.get("STATE_PATH", "/mnt/d/Bigdata/hero3_fresh/wsl2_train_state.pt")  # 模型+优化器联合保存


REWARD_SCALE = 1.0  # 奖励值 [-10,10] 无需缩放

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(264,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor, self.critic = nn.Linear(128,11), nn.Linear(128,1)
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)


def run_episode(mapname, blue_model=None):
    """Run one episode. If blue_model is given, pass --blue_model to ep_runner_one."""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    cmd = [VENV, RUNNER, str(STEPS_PER_EP), TRAJ, mapname]
    if blue_model:
        cmd.extend(["--blue_model", blue_model])
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )
    try: proc.wait(timeout=STEPS_PER_EP*3 + 15)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    try:
        with open(TRAJ) as f: d = json.load(f)
        if d.get("steps",0)>0 and not d.get("error"): return d
    except: pass
    return None


model = Net().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=LR)

def is_clean():
    """检查模型参数是否含 NaN/Inf"""
    for p in model.parameters():
        if torch.isnan(p).any() or torch.isinf(p).any():
            return False
    return True

def save_train_state(path, step=0):
    """保存模型+优化器+step计数"""
    torch.save({
        "model": model.state_dict(),
        "optimizer": opt.state_dict(),
        "step": step,
    }, path)

def save_shutdown(*args):
    """SIGTERM/SIGINT 时保存"""
    print("\n  Shutdown, saving train state...", flush=True)
    ckpt = f"/mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_shutdown_ckpt.pt"
    save_train_state(ckpt, total_steps)
    print(f"  Saved {ckpt}", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, save_shutdown)
signal.signal(signal.SIGINT, save_shutdown)


def restore_clean():
    """从最近的干净 checkpoint 恢复，没有则从零开始。重置 optimizer。"""
    global opt
    ckpt_dir = "/mnt/d/Bigdata/hero3_fresh/checkpoints"
    ckpts = sorted([f for f in os.listdir(ckpt_dir) if f.startswith("wsl2_ckpt_") and f.endswith(".pt") and "_model." not in f],
                   key=lambda f: int(f.replace("wsl2_ckpt_", "").replace(".pt", "")))
    for ckpt in reversed(ckpts):
        path = os.path.join(ckpt_dir, ckpt)
        if "_model." in ckpt:  # 跳过模型only文件（用于对手池，不是完整 checkpoint）
            continue
        try:
            sd = torch.load(path, map_location=DEVICE, weights_only=False)
            if "model" in sd:  # 新格式：dict 含 model/optimizer/step
                model.load_state_dict(sd["model"])
            else:  # 旧格式：直接是 state_dict
                model.load_state_dict(sd)
            if is_clean():
                print(f"  Restored clean checkpoint: {ckpt}", flush=True)
                # 重置 optimizer 防止 Adam 动量 NaN 残留
                global opt
                opt = torch.optim.Adam(model.parameters(), lr=LR)
                return
        except: pass
    # 全部失败则初始化新权重
    model.apply(lambda m: m.reset_parameters() if hasattr(m, 'reset_parameters') else None)
    print("  No clean checkpoint found, reinitialized model", flush=True)

# 尝试加载已有模型续训（优先加载联合状态 STATE_PATH）
if os.path.exists(STATE_PATH):
    try:
        sd = torch.load(STATE_PATH, map_location=DEVICE, weights_only=False)
        model.load_state_dict(sd["model"])
        if is_clean():
            opt.load_state_dict(sd["optimizer"])
            resume_step = sd.get("step", 0)
            print(f"Loaded train state (model+optimizer, step={resume_step})", flush=True)
        else:
            print("Loaded state has NaN model, restoring clean checkpoint...", flush=True)
            restore_clean()
    except Exception as e:
        print(f"Failed to load train state ({e}), falling back to model...", flush=True)
        # fallback to model-only
        if os.path.exists(MODEL_PATH):
            try:
                model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
                if is_clean():
                    print("Loaded existing model, continuing training", flush=True)
                else:
                    print("Loaded model contains NaN, restoring clean checkpoint...")
                    restore_clean()
            except:
                print("Failed to load model, restoring clean checkpoint...")
                restore_clean()
elif os.path.exists(MODEL_PATH):
    try:
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
        if is_clean():
            print("Loaded existing model, continuing training (fresh optimizer)", flush=True)
        else:
            print("Loaded model contains NaN, restoring clean checkpoint...", flush=True)
            restore_clean()
    except:
        print("Failed to load model, restoring clean checkpoint...", flush=True)
        restore_clean()

buffer = {"obs":[],"act":[],"rew":[],"nobs":[],"done":[]}
total_steps, ep_count, best_vloss, last_ckpt_step = 0, 0, float("inf"), 0

# === C3.2: 对手池初始化 ===
opponent_pool = []

print(f"WSL2 PPO — {N_EPISODES}eps×{STEPS_PER_EP}steps batch={BATCH} maps={len(MAPS)} device={DEVICE}", flush=True)
print(f" 自对弈: red=MMAI_USER blue=MMAI_USER/对手池", flush=True)
t0 = time.time()

for ep in range(N_EPISODES):
    # === C3.2: 选择对手 ===
    blue_model = None
    if opponent_pool:
        # 先清理已被删除的文件
        opponent_pool = [p for p in opponent_pool if os.path.exists(p)]
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

    if len(buffer["obs"]) >= BATCH:
        obs_t  = torch.tensor(np.array(buffer["obs"][:BATCH]), dtype=torch.float32, device=DEVICE)
        act_t  = torch.tensor(buffer["act"][:BATCH], dtype=torch.long, device=DEVICE)
        rew_t  = torch.tensor(buffer["rew"][:BATCH], dtype=torch.float32, device=DEVICE) * REWARD_SCALE
        nobs_t = torch.tensor(np.array(buffer["nobs"][:BATCH]), dtype=torch.float32, device=DEVICE)
        done_t = torch.tensor(buffer["done"][:BATCH], dtype=torch.float32, device=DEVICE)

        with torch.no_grad():
            pi_old, val_old = model(obs_t)
            logp_old = pi_old.log_prob(act_t)
            _, val_next = model(nobs_t)

        adv = rew_t + GAMMA * val_next * (1-done_t) - val_old
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)

        for epoch_i in range(EPOCHS):
            try:
                pi, val = model(obs_t)
            except ValueError:
                print(f"  NaN detected at epoch {epoch_i}, restoring clean checkpoint...", flush=True)
                restore_clean()
                break
            logp = pi.log_prob(act_t)
            ratio = (logp - logp_old).exp().clamp(max=100.0)  # 防数值溢出 inf
            surr = -torch.min(ratio*adv, torch.clamp(ratio,1-CLIP,1+CLIP)*adv).mean()
            vloss = nn.MSELoss()(val, rew_t + GAMMA*val_next.detach()*(1-done_t))
            loss = surr + 0.5*vloss - 0.01*pi.entropy().mean()
            opt.zero_grad(); loss.backward()

            # 检测梯度是否 NaN
            grad_ok = True
            for p in model.parameters():
                if p.grad is not None and (torch.isnan(p.grad).any() or torch.isinf(p.grad).any()):
                    grad_ok = False
                    break
            if not grad_ok:
                print(f"  NaN gradient at epoch {epoch_i}, restoring clean checkpoint...", flush=True)
                restore_clean()
                break

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            opt.step()

        for k in buffer: buffer[k] = buffer[k][BATCH:]
        elapsed = time.time() - t0
        print(f"  step{total_steps:>5d} avg_r={rew_t.mean():.1f} vloss={vloss.item():.0f} loss={loss.item():.0f} ep={ep_count} time={elapsed:.0f}s", flush=True)

        if vloss.item() < best_vloss and is_clean():
            best_vloss = vloss.item()
            save_train_state(STATE_PATH, total_steps)
        elif not is_clean():
            print("  NaN detected in model, restoring clean checkpoint...", flush=True)
            restore_clean()

        # === checkpoint: 每 200 step 保存，保留最近 OPPONENT_POOL_SIZE 个 ===
        ckpt_dir = "/mnt/d/Bigdata/hero3_fresh/checkpoints"
        os.makedirs(ckpt_dir, exist_ok=True)
        if total_steps - last_ckpt_step >= 200:
            last_ckpt_step = total_steps
            ckpt_path = os.path.join(ckpt_dir, f"wsl2_ckpt_{total_steps}.pt")
            model_only = ckpt_path.replace(".pt", "_model.pt")
            save_train_state(ckpt_path, total_steps)
            torch.save(model.state_dict(), model_only)

            # C3.2: 把 model-only 新 checkpoint 加入对手池
            if model_only not in opponent_pool:
                opponent_pool.append(model_only)
            if len(opponent_pool) > OPPONENT_POOL_SIZE:
                opponent_pool.pop(0)

            # 保留最近 OPPONENT_POOL_SIZE 个联合文件，删除旧的
            ckpts = sorted(
                [f for f in os.listdir(ckpt_dir)
                 if f.startswith("wsl2_ckpt_") and f.endswith(".pt") and "_model." not in f],
                key=lambda f: int(f.replace("wsl2_ckpt_", "").replace(".pt", ""))
            )
            for f in ckpts[:-OPPONENT_POOL_SIZE]:
                os.remove(os.path.join(ckpt_dir, f))
                # 同时删除对应的 model-only 文件
                mf = f.replace(".pt", "_model.pt")
                if os.path.exists(os.path.join(ckpt_dir, mf)):
                    os.remove(os.path.join(ckpt_dir, mf))

            # 清理对手池中已被删除的引用
            opponent_pool = [p for p in opponent_pool if os.path.exists(p)]

elapsed = time.time() - t0
print(f"\nDONE: {ep_count}eps {total_steps}steps {elapsed:.0f}s best_vloss={best_vloss:.0f}", flush=True)
if is_clean():
    sd = model.state_dict()
    has_bad = any(torch.isnan(v).any() or torch.isinf(v).any() for v in sd.values())
    if not has_bad:
        save_train_state(STATE_PATH, total_steps)
        torch.save(sd, MODEL_PATH)
        print("Final model+optimizer saved", flush=True)
    else:
        print("Final model has NaN, not saving", flush=True)
else:
    print("Final model has NaN, not saving", flush=True)
