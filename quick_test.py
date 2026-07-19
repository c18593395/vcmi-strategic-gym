import sys, os, time
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
from vcmi_gym.envs.v13.strategic_env import StrategicEnv, END_TURN

env = StrategicEnv(mapname="Key to Victory.h3m", max_turns=10,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error", vcmienv_loglevel="WARN",
    red="MMAI_USER", blue="StupidAI", random_heroes=1, boot_timeout=60, vcmi_timeout=10)

obs, _ = env.reset()
print(f"reset nz={sum(1 for x in obs if x>0)}", flush=True)

for i in range(5):
    t0 = time.time()
    try:
        obs, r, done, trunc, _ = env.step(END_TURN)
        dt = time.time() - t0
        print(f"step{i+1}: r={r:.1f} done={done or trunc} nz={sum(1 for x in obs if x>0)} dt={dt:.1f}s", flush=True)
        if done or trunc: break
    except Exception as e:
        print(f"step{i+1}: TIMEOUT after {time.time()-t0:.0f}s", flush=True)
        break
print("DONE", flush=True)
