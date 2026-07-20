import sys, os, json, time, traceback
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

mapname = sys.argv[3] if len(sys.argv) > 3 else "Key to Victory.h3m"
outfile = sys.argv[2] if len(sys.argv) > 2 else "/tmp/traj_one.json"

print("INIT", flush=True)
env = StrategicEnv(
    mapname=mapname, max_turns=1,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    vcmienv_loglevel="ERROR", red="MMAI_USER", blue="StupidAI",
    random_heroes=1, boot_timeout=60, vcmi_timeout=30
)

print("RESET", flush=True)
obs, info = env.reset()
nz = sum(1 for x in obs if x > 0)
print(f"RESET OK nz={nz} player={info.get('current_player','?')}", flush=True)

print("STEP", flush=True)
a = int(env.action_space.sample())
nobs, r, done, trunc, info2 = env.step(a)
nz2 = sum(1 for x in nobs if x > 0)
print(f"STEP OK r={r:.1f} done={done} nz={nz2}", flush=True)

traj = {"obs":[obs.tolist()],"act":[a],"rew":[float(r)],"nobs":[nobs.tolist()],"done":[bool(done)],"steps":1,"total_rew":float(r)}
with open(outfile, "w") as f:
    json.dump(traj, f)
print("JSON WRITTEN", flush=True)
os._exit(0)
