#!/usr/bin/env python3
"""T14.3 load proof probe: boot KTV with blue_adventure_ai=T14Blue / Nullkiller2,
loglevelAI=info, capture [T14-ACT] lines to confirm gateway instantiation.

Deployed on server 09-26 as /DATA/hero3/t14load_probe.py (scp'd from local).
Run (server, with env — bare run fails on default WSL STRATEGIC_STATE_LIB):
  env STRATEGIC_STATE_LIB=/DATA/hero3/vcmi-build/bin/libmlclient.so \
      LD_LIBRARY_PATH=/DATA/hero3/vcmi-build/bin DISPLAY=:99 \
      VCMI_WORKSPACE_DIR=/root/vcmi-workspace VCMI_NATIVE_DIR=/DATA/hero3/vcmi \
      PYTHONPATH=/DATA/hero3/vcmi_gym_new:/DATA/hero3 HERO3_ROOT=/DATA/hero3 \
      python3 py/t14load_probe.py
Expected for T14Blue arm: [T14-ACT] T14Blue resolved archetype=P? aggr=? seed=... map=...
"""
import sys, os, traceback
R = os.environ.get("HERO3_ROOT", "/DATA/hero3")
sys.path.insert(0, R + "/vcmi_gym_new")
import vcmi_gym.envs.v13.strategic_env as se
MP = "Key to Victory.h3m"
os.environ.setdefault("VCMI_WORKSPACE_DIR", "/root/vcmi-workspace")
for arm in ["T14Blue", "Nullkiller2"]:
    print(f"=== ARM {arm} ===", flush=True)
    try:
        env = se.StrategicEnv(mapname=MP, boot_timeout=300, max_turns=8,
            red="StupidAI", blue="StupidAI", blue_adventure_ai=arm,
            vcmienv_loglevel="ERROR",
            vcmi_loglevel_global="error",
            vcmi_loglevel_ai="info")
        obs, info = env.reset()
        print("BOOTED", flush=True)
        for i in range(6):
            obs, rew, term, trunc, info = env.step(10)
            print(f"step{i} rew={rew:.2f} term={term}", flush=True)
            if term or trunc: break
        try: env.close()
        except Exception as e: print("close:", e, flush=True)
    except Exception:
        traceback.print_exc()
    print(f"=== ARM {arm} DONE ===", flush=True)
print("PROBE_DONE", flush=True)
