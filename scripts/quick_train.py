#!/usr/bin/env python3
"""Quick 3-episode test of subprocess-per-episode PPO training"""
import subprocess, json, time, sys, os

sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

MAPNAME = "Key to Victory.h3m"
TRAJ_JSON = "/tmp/traj_latest.json"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner.py"
VENV_PYTHON = "/home/administrator/vcmi-workspace/venv/bin/python"

for ep in range(3):
    t0 = time.time()
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    proc = None
    try:
        proc = subprocess.Popen(
            [VENV_PYTHON, "-u", RUNNER, "10", TRAJ_JSON, MAPNAME],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
        )
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        if proc: proc.kill()
    finally:
        if proc:
            try: proc.kill()
            except: pass
    try:
        with open(TRAJ_JSON, "r") as f:
            info = json.load(f)
        print(f"ep {ep+1}: steps={info['steps']} rew={info['rew']:.1f} time={time.time()-t0:.1f}s", flush=True)
    except:
        print(f"ep {ep+1}: FAIL time={time.time()-t0:.1f}s", flush=True)

print("DONE", flush=True)
