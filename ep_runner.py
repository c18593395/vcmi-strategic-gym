#!/usr/bin/env python3
"""Episode runner — called from WSL subprocess"""
import sys, os, pickle, json
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
import numpy as np
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

max_turns = int(sys.argv[1]) if len(sys.argv) > 1 else 20
outfile = sys.argv[2] if len(sys.argv) > 2 else "/mnt/d/Bigdata/hero3_fresh/traj_latest.pkl"

env = StrategicEnv(mapname="adventure-A1.vmap", max_turns=max_turns,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    vcmienv_loglevel="ERROR", red="MMAI_USER", blue="StupidAI",
    random_heroes=1, boot_timeout=60)

obs, _ = env.reset()
traj = {"obs": [], "act": [], "rew": [], "nobs": [], "done": []}
for _ in range(max_turns):
    o = obs.copy()
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
# Also write JSON summary to separate file
jsonfile = outfile.replace(".pkl", ".json")
with open(jsonfile, "w") as f:
    json.dump({"steps": len(traj["obs"]), "rew": sum(traj["rew"])}, f)
sys.stdout.write(json.dumps({"steps": len(traj["obs"]), "rew": sum(traj["rew"])}) + "\n")
sys.stdout.flush()
