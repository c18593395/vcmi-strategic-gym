import sys, os
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
from vcmi_gym.envs.v13.strategic_env import StrategicEnv
env = StrategicEnv(mapname="Key to Victory.h3m", max_turns=5,
    vcmi_loglevel_global="error", vcmienv_loglevel="ERROR",
    red="MMAI", blue="StupidAI", random_heroes=1, boot_timeout=60, vcmi_timeout=60)
obs, _ = env.reset()
prev = (float(obs[106]), float(obs[107]))
print("RESET h0=(%d,%d) nz=%d" % (obs[106], obs[107], sum(1 for x in obs if x)), flush=True)
for i in range(5):
    nobs, r, d, t, _ = env.step(i % 8)
    cur = (float(nobs[106]), float(nobs[107]))
    m = " MOVED" if cur != prev else ""
    print("step=%d r=%.2f h0=(%.0f,%.0f) nz=%d%s" % (i, r, cur[0], cur[1], sum(1 for x in nobs if x), m), flush=True)
    prev = cur
    if d: break
env.close()
os._exit(0)
