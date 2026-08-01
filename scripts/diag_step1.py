#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C8.5 诊断: 观察 step 后终止原因 (ep_steps=1 根因)"""
import sys, time, os
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

env = StrategicEnv(
    mapname="Dungeon Keeper.h3m", max_turns=5,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    vcmienv_loglevel="DEBUG", red="StupidAI", blue="StupidAI",
    random_heroes=1, boot_timeout=120, vcmi_timeout=120,
    red_adventure_ai="MMAI", blue_adventure_ai="Nullkiller2",
    reward_explore=1.0,
)
t0 = time.time()
obs, info = env.reset()
print(f"[diag] reset {time.time()-t0:.0f}s info={info} obs_nz={(obs>0).sum()}")
print(f"[diag] send act=8 (交互)")
t1 = time.time()
try:
    nobs, r, term, trunc, info2 = env.step(8)
    print(f"[diag] step(8) {time.time()-t1:.0f}s r={r} term={term} trunc={trunc} info={info2}")
except Exception as e:
    print(f"[diag] step(8) EXC {time.time()-t1:.0f}s: {e}")
env.close()
print("[diag] done")
