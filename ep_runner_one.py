import sys, os, json
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

max_turns = int(sys.argv[1]) if len(sys.argv) > 1 else 10
outfile = sys.argv[2] if len(sys.argv) > 2 else "/tmp/traj_one.json"
mapname = sys.argv[3] if len(sys.argv) > 3 else "Key to Victory.h3m"

traj = {"obs": [], "act": [], "rew": [], "nobs": [], "done": [], "steps": 0, "total_rew": 0.0}
try:
    env = StrategicEnv(
        mapname=mapname, max_turns=max_turns,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR", red="MMAI_USER", blue="MMAI_USER",
        random_heroes=1, boot_timeout=60, vcmi_timeout=15
    )
    obs, _ = env.reset()
    for _ in range(max_turns):
        a = int(env.action_space.sample())
        nobs, r, done, trunc, _ = env.step(a)
        traj["obs"].append(obs.tolist())
        traj["act"].append(a)
        traj["rew"].append(float(r))
        traj["nobs"].append(nobs.tolist())
        traj["done"].append(bool(done or trunc))
        traj["steps"] += 1
        obs = nobs
        if done or trunc: break
except Exception as e:
    traj["error"] = str(e)

traj["total_rew"] = sum(traj["rew"])
with open(outfile, "w") as f:
    json.dump(traj, f); f.flush(); os.fsync(f.fileno())
os._exit(0)
