#!/usr/bin/env python3
"""C1 baseline — adventure-A1.vmap random agent multi-step"""
import sys, os, time, numpy as np
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ.setdefault("STRATEGIC_STATE_LIB",
    "/home/administrator/vcmi-native/rel/bin/libmlclient.so")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

env = StrategicEnv(mapname="adventure-A1.vmap", boot_timeout=30,
    random_heroes=1, max_turns=20,
    red="MMAI_USER", blue="StupidAI",
    vcmienv_loglevel="WARN", vcmi_loglevel_global="error",
    vcmi_loglevel_ai="error")

t0 = time.time()
obs, info = env.reset()
print(f"reset nz={np.count_nonzero(obs)} dt={time.time()-t0:.1f}s", flush=True)

ep_rew = 0.0
for i in range(20):
    t1 = time.time()
    action = env.action_space.sample()
    obs, rew, term, trunc, info = env.step(int(action))
    ep_rew += rew
    print(f"  s{i:02d} a={action} r={rew:+.2f} tot={ep_rew:.2f} nz={np.count_nonzero(obs)} dt={time.time()-t1:.1f}s", flush=True)
    if term or trunc: break

print(f"done: rew={ep_rew:.2f} steps={i+1} total={time.time()-t0:.0f}s", flush=True)
env.close()
