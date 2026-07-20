"""Quick diag test — Phase C spinloop check"""
import sys, os
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

from vcmi_gym.envs.v13.strategic_env import StrategicEnv
import numpy as np

env = StrategicEnv(
    mapname="adventure-A1.vmap", max_turns=1,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    vcmienv_loglevel="ERROR", red="MMAI_USER", blue="StupidAI",
    random_heroes=0, boot_timeout=30,
)
print(">>> reset...")
obs, info = env.reset()
print(f">>> RESET OK: nonzero={np.count_nonzero(obs)}")
env.close()
print("DONE")
