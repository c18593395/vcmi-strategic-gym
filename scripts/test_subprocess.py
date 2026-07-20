#!/usr/bin/env python3
"""Quick test: subprocess episode → JSON → read"""
import subprocess, json, time, os

VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
TRAJ = "/tmp/traj_one.json"

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

for i in range(3):
    t0 = time.time()
    p = subprocess.Popen(
        [VENV, RUNNER, "1", TRAJ, "Key to Victory.h3m"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait()
    dt = time.time() - t0
    try:
        d = json.load(open(TRAJ))
        obs = d["obs"][0]
        nz = sum(1 for x in obs if x > 0)
        print(f"ep{i+1}: nz={nz} steps={d['steps']} err={d['error']} dt={dt:.1f}s rc={p.returncode}")
    except Exception as e:
        print(f"ep{i+1}: FAIL {e} dt={dt:.1f}s")

print("DONE")
