import sys, os, json, argparse
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

parser = argparse.ArgumentParser()
parser.add_argument("max_turns", nargs="?", type=int, default=10)
parser.add_argument("outfile", nargs="?", type=str, default="/tmp/traj_one.json")
parser.add_argument("mapname", nargs="?", type=str, default="Key to Victory.h3m")
parser.add_argument("--blue_model", type=str, default=None,
                    help="Path to blue model checkpoint")
parser.add_argument("--blue_ai", type=str, default=None,
                    help="AI type for blue player (MMAI_USER, StupidAI, etc.)")
args = parser.parse_args()

# --blue_model: use ML model as blue
blue = "MMAI_USER"
if args.blue_model:
    blue = "ML_USER"
    os.environ["ML_MODEL_PATH"] = args.blue_model
# --blue_ai: directly override blue AI type (takes precedence)
if args.blue_ai:
    blue = args.blue_ai

traj = {"obs": [], "act": [], "rew": [], "nobs": [], "done": [], "steps": 0, "total_rew": 0.0}
try:
    env = StrategicEnv(
        mapname=args.mapname, max_turns=args.max_turns,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR", red="MMAI", blue=blue,
        random_heroes=1, boot_timeout=60, vcmi_timeout=15
    )
    obs, _ = env.reset()
    for _ in range(args.max_turns):
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
with open(args.outfile, "w") as f:
    json.dump(traj, f); f.flush(); os.fsync(f.fileno())
os._exit(0)
