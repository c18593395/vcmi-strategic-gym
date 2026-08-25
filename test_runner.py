import subprocess, os

VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
TRAJ = "/tmp/traj_test.json"
MODEL_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model_level0.pt"

mapname = "T01_adventure_20X20_01.vmap"

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

cmd = [VENV, RUNNER, "50", TRAJ, mapname]
if os.path.exists(MODEL_PATH):
    cmd.extend(["--model", MODEL_PATH])

print(f"Running: {' '.join(cmd)}")
proc = subprocess.Popen(cmd, env=env)
proc.wait(timeout=120)
print(f"Exit code: {proc.returncode}")

if os.path.exists(TRAJ):
    import json
    with open(TRAJ) as f:
        d = json.load(f)
    print(f"Trajectory: steps={d.get('steps', 0)}, error={d.get('error', 'none')}")
