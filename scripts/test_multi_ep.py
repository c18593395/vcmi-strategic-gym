#!/usr/bin/env python3
"""Multi-episode test: new env per episode"""
import sys, os, numpy as np
sys.path.insert(0, "/home/administrator/vcmi-workspace")
os.environ.setdefault("STRATEGIC_STATE_LIB",
    "/home/administrator/vcmi-native/rel/bin/libmlclient.so")
import gymnasium as gym
import vcmi_gym.envs.v13.strategic_env

def make_env():
    return gym.make("VCMI-strategic-v1",
        mapname="adventure-A1.vmap",
        boot_timeout=30, random_heroes=0,
        max_turns=3,
        vcmienv_loglevel="WARN",
        vcmi_loglevel_global="error",
    )

print("=== Multi-episode test (3 eps, max_turns=3, fresh env each) ===", flush=True)

for ep in range(3):
    print(f"\n--- Episode {ep+1} (new env) ---", flush=True)
    env = make_env()
    obs, info = env.reset()
    print(f"  reset: nonzero={obs.nonzero()[0].shape[0]}, day={info['day']}", flush=True)
    
    ep_rew = 0.0
    for step in range(5):
        obs, rew, term, trunc, info = env.step(10)
        ep_rew += rew
        print(f"  step {step}: rew={rew:.2f} tot={ep_rew:.2f} done={term or trunc}", flush=True)
        if term or trunc:
            break
    
    print(f"  episode reward: {ep_rew:.2f}", flush=True)
    env.close()

print("\n=== ALL OK ===", flush=True)
