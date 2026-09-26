#!/usr/bin/env python3
import sys, os, traceback
R = os.environ.get("HERO3_ROOT", "/DATA/hero3")
sys.path.insert(0, R + "/vcmi_gym_new")
import vcmi_gym.envs.v13.strategic_env as se
MP = "Key to Victory.h3m"
os.environ.setdefault("VCMI_WORKSPACE_DIR","/root/vcmi-workspace")
for arm in ["T14Blue","Nullkiller2"]:
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
