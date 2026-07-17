#!/usr/bin/env python3
"""C1 PPO Training — WSL subprocess, timeout-tolerant"""
import subprocess, json, time, pickle, os
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

OBS_DIM, N_ACTIONS = 256, 11
N_EPISODES, MAX_TURNS = 50, 20
LR, GAMMA, CLIP, EPOCHS = 3e-4, 0.99, 0.2, 4
TRAJ = r"D:\Bigdata\hero3_fresh\traj_latest.pkl"
TRAJ_JSON = r"D:\Bigdata\hero3_fresh\traj_latest.json"
MODEL = r"D:\Bigdata\hero3_fresh\c1_model.pt"
BASH = r"C:\Program Files\Git\bin\bash.exe"

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(256,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor = nn.Linear(128, 11)
        self.critic = nn.Linear(128, 1)
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

model = Net()
opt = torch.optim.Adam(model.parameters(), lr=LR)

WSL_SCRIPT = '/d/Bigdata/hero3_fresh/_ep_tmp.sh'

def run_episode(turns):
    script = f'''#!/bin/bash
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash -c "
source /home/administrator/vcmi-workspace/venv/bin/activate
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
cd /home/administrator/vcmi-workspace
timeout 30 python3 -u /mnt/d/Bigdata/hero3_fresh/ep_runner.py {turns} /mnt/d/Bigdata/hero3_fresh/traj_latest.pkl 2>/dev/null
"'''
    with open(WSL_SCRIPT, 'w') as f:
        f.write(script)
    try:
        r = subprocess.run([BASH, WSL_SCRIPT], capture_output=True, timeout=45)
        out = r.stdout.decode('utf-8', errors='replace').strip()
    except subprocess.TimeoutExpired:
        out = ""  # OK, data already written to pickle+json
    
    # Try JSON file first (more reliable than stdout)
    try:
        with open(TRAJ_JSON, 'r') as f:
            return json.load(f)
    except:
        pass
    
    for line in reversed(out.split('\n') if out else []):
        try: return json.loads(line)
        except: pass
    
    # Fallback: read pickle directly
    try:
        with open(TRAJ, "rb") as f:
            traj = pickle.load(f)
        return {"steps": len(traj["obs"]), "rew": sum(traj["rew"])}
    except:
        return {"steps": 0, "rew": 0.0}

print(f"C1 PPO — {N_EPISODES}ep x {MAX_TURNS}t", flush=True)
t_start = time.time()

for ep in range(N_EPISODES):
    t0 = time.time()
    info = run_episode(MAX_TURNS)
    if info["steps"] == 0:
        print(f"  ep{ep:03d} NO_DATA", flush=True); continue

    with open(TRAJ, "rb") as f: traj = pickle.load(f)
    obs = torch.tensor(traj["obs"], dtype=torch.float32)
    acts = torch.tensor(traj["act"], dtype=torch.long)
    rews = torch.tensor(traj["rew"], dtype=torch.float32)
    dones = torch.tensor(traj["done"], dtype=torch.float32)

    rets = torch.zeros_like(rews); R = 0.0
    for t in reversed(range(len(rews))):
        R = rews[t] + GAMMA * R * (1 - dones[t]); rets[t] = R

    with torch.no_grad():
        old_pi, _ = model(obs); old_lp = old_pi.log_prob(acts)

    for _ in range(EPOCHS):
        pi, vals = model(obs)
        ratio = (pi.log_prob(acts) - old_lp).exp()
        adv = rets - vals.detach()
        s1 = ratio * adv; s2 = torch.clamp(ratio, 1-CLIP, 1+CLIP) * adv
        loss = -torch.min(s1, s2).mean() + 0.5 * (rets - vals).pow(2).mean()
        opt.zero_grad(); loss.backward(); opt.step()

    dt = time.time() - t0
    eta = (time.time() - t_start) / (ep + 1) * (N_EPISODES - ep - 1)
    print(f"  ep{ep:03d} s={info['steps']} r={info['rew']:+.1f} L={loss.item():.3f} dt={dt:.0f}s ETA={eta:.0f}s", flush=True)

torch.save(model.state_dict(), MODEL)
print(f"\nSaved {MODEL}  total={time.time()-t_start:.0f}s", flush=True)
