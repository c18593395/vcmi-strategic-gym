#!/usr/bin/env python3
"""Multi-episode test: single env, let step timeout end the episode"""
import sys, os, numpy as np
sys.path.insert(0, "/home/administrator/vcmi-workspace")
os.environ.setdefault("STRATEGIC_STATE_LIB",
    "/home/administrator/vcmi-native/rel/bin/libmlclient.so")
import gymnasium as gym
import vcmi_gym.envs.v13.strategic_env

print("=== Single env, 2 eps, max_turns=3 ===", flush=True)

env = gym.make("VCMI-strategic-v1",
    mapname="adventure-A1.vmap",
    boot_timeout=30, random_heroes=0,
    max_turns=3,
    vcmienv_loglevel="WARN",
    vcmi_loglevel_global="error",
)

for ep in range(3):
    print(f"\n--- Episode {ep+1} ---", flush=True)
    obs, info = env.reset()
    print(f"  reset: nonzero={obs.nonzero()[0].shape[0]}", flush=True)
    
    ep_rew = 0.0
    for s in range(5):
        obs, rew, term, trunc, info = env.step(10)
        ep_rew += rew
        print(f"  step {s}: rew={rew:.2f} tot={ep_rew:.2f} d={term or trunc}", flush=True)
        if term or trunc:
            print(f"  episode done at step {s}", flush=True)
            break

print(f"\nFinal reward: {ep_rew:.2f}", flush=True)
env.close()
print("DONE", flush=True)
