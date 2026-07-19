#!/usr/bin/env python3
"""WSL2 PPO — multi-step episodes, real states, real rewards"""
import subprocess, json, time, os, random
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

N_EPISODES, BATCH, STEPS_PER_EP = 50, 16, 5
LR, CLIP, EPOCHS = 3e-4, 0.2, 4
MAPS = [
    "Key to Victory.h3m", "Elbow Room.h3m", "Emerald Isles.h3m",
    "Golems Aplenty.h3m", "A Warm and Familiar Place.h3m",
    "All for One.h3m", "A Viking We Shall Go.h3m", "Dead and Buried.h3m",
]
VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
TRAJ = "/tmp/traj_one.json"

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(256,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor, self.critic = nn.Linear(128,11), nn.Linear(128,1)
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

def run_episode(mapname):
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    proc = subprocess.Popen(
        [VENV, RUNNER, str(STEPS_PER_EP), TRAJ, mapname],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill(); proc.wait()
    try:
        with open(TRAJ) as f:
            d = json.load(f)
        if d.get("steps", 0) > 0 and not d.get("error"):
            return d
    except: pass
    return None

model = Net()
opt = torch.optim.Adam(model.parameters(), lr=LR)
buffer = {"obs":[], "act":[], "rew":[], "nobs":[], "done":[]}
total_steps, ep_count = 0, 0

print(f"WSL2 PPO — {N_EPISODES}eps x{STEPS_PER_EP}steps batch={BATCH} maps={len(MAPS)}", flush=True)
t0 = time.time()

for ep in range(N_EPISODES):
    traj = run_episode(random.choice(MAPS))
    ep_count += 1
    if traj is None:
        continue
    for i in range(traj["steps"]):
        for k in ["obs","act","rew","nobs","done"]:
            buffer[k].append(traj[k][i])
        total_steps += 1
    if len(buffer["obs"]) >= BATCH:
        obs_t = torch.tensor(np.array(buffer["obs"][:BATCH]), dtype=torch.float32)
        act_t = torch.tensor(buffer["act"][:BATCH], dtype=torch.long)
        rew_t = torch.tensor(buffer["rew"][:BATCH], dtype=torch.float32)
        nobs_t = torch.tensor(np.array(buffer["nobs"][:BATCH]), dtype=torch.float32)
        done_t = torch.tensor(buffer["done"][:BATCH], dtype=torch.float32)

        with torch.no_grad():
            pi_old, val_old = model(obs_t)
            logp_old = pi_old.log_prob(act_t)
            _, val_next = model(nobs_t)
        
        # Advantage = r + gamma*V(next)*(1-done) - V(curr)
        adv = rew_t + 0.99 * val_next * (1 - done_t) - val_old
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        
        for _ in range(EPOCHS):
            pi, val = model(obs_t)
            logp = pi.log_prob(act_t)
            ratio = (logp - logp_old).exp()
            surr = -torch.min(ratio * adv, torch.clamp(ratio, 1-CLIP, 1+CLIP) * adv).mean()
            vloss = nn.MSELoss()(val, rew_t + 0.99 * val_next.detach() * (1 - done_t))
            loss = surr + 0.5 * vloss - 0.01 * pi.entropy().mean()
            opt.zero_grad(); loss.backward(); opt.step()
        
        for k in buffer: buffer[k] = buffer[k][BATCH:]
        elapsed = time.time() - t0
        print(f"  batch {total_steps}steps avg_r={rew_t.mean():.1f} vloss={vloss.item():.1f} loss={loss.item():.1f} time={elapsed:.0f}s", flush=True)

elapsed = time.time() - t0
print(f"DONE: {ep_count}eps {total_steps}steps {elapsed:.0f}s", flush=True)
torch.save(model.state_dict(), "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt")
