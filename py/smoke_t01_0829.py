# -*- coding: utf-8 -*-
"""0829 对照: T01 空地图移动测试 — 区分 .so 对坏 vs 地图特有问题. PASS = 至少一次移动被接受(r>-1.2)"""
import os, sys, time
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

env = StrategicEnv(
    mapname="T01_adventure_20X20_01.vmap", max_turns=5,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    vcmienv_loglevel="ERROR", red="StupidAI", blue="StupidAI",
    random_heroes=0, boot_timeout=120, vcmi_timeout=900,
)
obs, info = env.reset()
print(f"[t01] reset OK obs_nz={(obs>0).sum()}")
ok = 0
for s in range(16):
    a = 24 if s < 8 else s % 8
    obs, r, term, trunc, info = env.step(a)
    if r > -1.2:
        ok += 1
    print(f"[t01] step={s} act={a} r={r:.2f} term={term} trunc={trunc}")
    if term or trunc:
        break
env.close()
print(f"[t01] RESULT accepted_moves={ok} -> {'PASS' if ok else 'FAIL'}")
