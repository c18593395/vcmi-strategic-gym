#!/usr/bin/env python3
"""Episode runner — model policy or random"""
import sys, os, pickle, json
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
import numpy as np
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

max_turns = int(sys.argv[1]) if len(sys.argv) > 1 else 20
outfile = sys.argv[2] if len(sys.argv) > 2 else "/mnt/d/Bigdata/hero3_fresh/traj_latest.pkl"
mapname = sys.argv[3] if len(sys.argv) > 3 else "adventure-A1.vmap"
model_path = sys.argv[4] if len(sys.argv) > 4 else ""

# Load model if provided
model = None
if model_path and os.path.exists(model_path):
    import torch, torch.nn as nn
    from torch.distributions import Categorical
    class Net(nn.Module):
        def __init__(self):super().__init__();self.fc=nn.Sequential(nn.Linear(256,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU());self.actor=nn.Linear(128,11);self.critic=nn.Linear(128,1)
        def forward(self,x):h=self.fc(x);return Categorical(logits=self.actor(h)),self.critic(h).squeeze(-1)
    model=Net()
    model.load_state_dict(torch.load(model_path))
    model.eval()

env = StrategicEnv(mapname=mapname, max_turns=max_turns,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    vcmienv_loglevel="ERROR", red="MMAI_USER", blue="StupidAI",
    random_heroes=1, boot_timeout=60)

obs, _ = env.reset()
traj = {"obs": [], "act": [], "rew": [], "nobs": [], "done": []}
for _ in range(max_turns):
    o = obs.copy()
    if model:
        with torch.no_grad():
            pi, _ = model(torch.tensor(o, dtype=torch.float32).unsqueeze(0))
        a = int(pi.sample().item())
    else:
        a = int(env.action_space.sample())
    nobs, r, done, trunc, _ = env.step(a)
    traj["obs"].append(o.tolist())
    traj["act"].append(a)
    traj["rew"].append(float(r))
    traj["nobs"].append(nobs.tolist())
    traj["done"].append(bool(done or trunc))
    obs = nobs
    if done or trunc:
        break
with open(outfile, "wb") as f:
    pickle.dump(traj, f)
jsonfile = outfile.replace(".pkl", ".json")
with open(jsonfile, "w") as f:
    json.dump({"steps": len(traj["obs"]), "rew": sum(traj["rew"])}, f)
sys.stdout.write(json.dumps({"steps": len(traj["obs"]), "rew": sum(traj["rew"])}) + "\n")
sys.stdout.flush()
