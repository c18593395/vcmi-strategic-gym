#!/usr/bin/env python3
"""Single-episode test: both sides StupidAI"""
import sys, os, time, numpy as np
sys.path.insert(0, "/home/administrator/vcmi-workspace")
os.environ.setdefault("STRATEGIC_STATE_LIB",
    "/home/administrator/vcmi-native/rel/bin/libmlclient.so")
import vcmi_gym.envs.v13.strategic_env as se

print("=== Rollout (StupidAI both sides) ===", flush=True)
env = se.StrategicEnv(mapname="adventure-A1.vmap", boot_timeout=30,
    random_heroes=0, max_turns=8, reward_step_fixed=-0.1,
    red="StupidAI", blue="StupidAI",
    vcmienv_loglevel="WARN", vcmi_loglevel_global="error")

t0 = time.time()
obs, info = env.reset()
print(f"reset: {time.time()-t0:.0f}s nonzero={obs.nonzero()[0].shape[0]}", flush=True)

ep_rew = 0.0
for i in range(8):
    t1 = time.time()
    action = env.action_space.sample()
    obs, rew, term, trunc, info = env.step(int(action))
    ep_rew += rew
    print(f"  step {i}: rew={rew:.2f} tot={ep_rew:.2f} ({time.time()-t1:.0f}s)", flush=True)
    if term or trunc: break
print(f"done: rew={ep_rew:.2f} total={time.time()-t0:.0f}s", flush=True)
