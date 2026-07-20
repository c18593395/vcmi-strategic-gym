#!/usr/bin/env python3
"""WSL2 PPO — 多步自对弈训练 (GPU) — C3.2+C4.2"""
import subprocess, json, time, os, random
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

# === C4.2: 扩规模 ===
N_EPISODES, BATCH, STEPS_PER_EP = 2000, 128, 50
LR, CLIP, EPOCHS = 3e-4, 0.2, 4
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

VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
TRAJ = "/tmp/traj_one.json"
MODEL_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt"


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(256,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
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
# 尝试加载已有模型续训
if os.path.exists(MODEL_PATH):
    try:
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
        print("Loaded existing model, continuing training", flush=True)
    except: pass

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
        rew_t  = torch.tensor(buffer["rew"][:BATCH], dtype=torch.float32, device=DEVICE)
        nobs_t = torch.tensor(np.array(buffer["nobs"][:BATCH]), dtype=torch.float32, device=DEVICE)
        done_t = torch.tensor(buffer["done"][:BATCH], dtype=torch.float32, device=DEVICE)

        with torch.no_grad():
            pi_old, val_old = model(obs_t)
            logp_old = pi_old.log_prob(act_t)
            _, val_next = model(nobs_t)

        adv = rew_t + GAMMA * val_next * (1-done_t) - val_old
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)

        for _ in range(EPOCHS):
            pi, val = model(obs_t)
            logp = pi.log_prob(act_t)
            ratio = (logp - logp_old).exp()
            surr = -torch.min(ratio*adv, torch.clamp(ratio,1-CLIP,1+CLIP)*adv).mean()
            vloss = nn.MSELoss()(val, rew_t + GAMMA*val_next.detach()*(1-done_t))
            loss = surr + 0.5*vloss - 0.01*pi.entropy().mean()
            opt.zero_grad(); loss.backward(); opt.step()

        for k in buffer: buffer[k] = buffer[k][BATCH:]
        elapsed = time.time() - t0
        print(f"  step{total_steps:>5d} avg_r={rew_t.mean():.1f} vloss={vloss.item():.0f} loss={loss.item():.0f} ep={ep_count} time={elapsed:.0f}s", flush=True)

        if vloss.item() < best_vloss:
            best_vloss = vloss.item()
            torch.save(model.state_dict(), MODEL_PATH)

        # === checkpoint: 每 200 step 保存，保留最近 OPPONENT_POOL_SIZE 个 ===
        ckpt_dir = "/mnt/d/Bigdata/hero3_fresh/checkpoints"
        os.makedirs(ckpt_dir, exist_ok=True)
        if total_steps - last_ckpt_step >= 200:
            last_ckpt_step = total_steps
            ckpt_path = os.path.join(ckpt_dir, f"wsl2_ckpt_{total_steps}.pt")
            torch.save(model.state_dict(), ckpt_path)

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
