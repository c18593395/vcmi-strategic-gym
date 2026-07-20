#!/usr/bin/env python3
"""Test 3 single-step episodes (max_turns=1)"""
import subprocess, json, time, os

VENV_PYTHON = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
TRAJ_JSON = "/tmp/traj_one.json"

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

for ep in range(5):
    t0 = time.time()
    proc = None
    try:
        proc = subprocess.Popen(
            [VENV_PYTHON, "-u", RUNNER, "1", TRAJ_JSON, "Key to Victory.h3m"],
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
        with open(TRAJ_JSON) as f:
            d = json.load(f)
        print(f"ep{ep+1}: steps={d['steps']} rew={d['total_rew']:.1f} err={d.get('error','none')} time={time.time()-t0:.1f}s", flush=True)
    except:
        print(f"ep{ep+1}: FAIL time={time.time()-t0:.1f}s", flush=True)

print("DONE", flush=True)
