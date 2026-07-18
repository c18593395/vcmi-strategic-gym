#!/usr/bin/env python3
"""C2 PPO Training — vs StupidAI on Key to Victory.h3m, nonzero=44"""
import subprocess, json, time, pickle, sys, os
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

N_EPISODES, MAX_TURNS = 100, 30
LR, GAMMA, CLIP, EPOCHS = 3e-4, 0.99, 0.2, 4
TRAJ_PKL = "/mnt/d/Bigdata/hero3_fresh/traj_latest.pkl"
TRAJ_JSON = "/mnt/d/Bigdata/hero3_fresh/traj_latest.json"
MODEL = "/mnt/d/Bigdata/hero3_fresh/c2_model.pt"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner.py"
MAPNAME = "adventure-A1.vmap"  # fast test, switch to Key to Victory.h3m for real

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(256,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor = nn.Linear(128, 11)
        self.critic = nn.Linear(128, 1)
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

def run_episode(turns):
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    proc = None
    try:
        proc = subprocess.Popen([sys.executable, "-u", RUNNER, str(turns), TRAJ_PKL, MAPNAME],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        if proc: proc.kill()
    finally:
        if proc:
            try: proc.kill()
            except: pass
    try:
        with open(TRAJ_JSON, 'r') as f: return json.load(f)
    except:
        return {"steps": 0, "rew": 0.0}

model = Net()
opt = torch.optim.Adam(model.parameters(), lr=LR)
print(f"C2 PPO — {N_EPISODES}ep x {MAX_TURNS}t  map={MAPNAME}", flush=True)
t_start = time.time()

for ep in range(N_EPISODES):
    t0 = time.time()
    info = run_episode(MAX_TURNS)
    if info["steps"] == 0:
        print(f"  ep{ep:03d} NO_DATA", flush=True); continue

    with open(TRAJ_PKL, "rb") as f: traj = pickle.load(f)
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
print(f"Saved {MODEL} total={time.time()-t_start:.0f}s", flush=True)
