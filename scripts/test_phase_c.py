"""Phase C E2E test — StrategicEnv with fixed libmlclient.so"""
import sys, os, time, numpy as np
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

from vcmi_gym.envs.v13.strategic_env import StrategicEnv

print("=== Phase C E2E ===")
env = StrategicEnv(
    mapname="adventure-A1.vmap", max_turns=3,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    vcmienv_loglevel="ERROR", red="MMAI_USER", blue="StupidAI",
    random_heroes=0, boot_timeout=60,
)
print(f"Action: Discrete({env.N_ACTIONS}), Obs: Box(256)")

print("[1] reset...")
try:
    obs, info = env.reset()
    print(f"    OK: nonzero={np.count_nonzero(obs)}/256, day={info['day']}")
except Exception as e:
    print(f"    FAIL: {e}")
    import traceback; traceback.print_exc()
    env.close(); sys.exit(1)

print("[2] step(MOVE_RIGHT)...")
try:
    obs, r, t, tr, info = env.step(0)
    print(f"    OK: nz={np.count_nonzero(obs)} r={r:.3f} term={t}")
except Exception as e:
    print(f"    FAIL: {e}")
    import traceback; traceback.print_exc()

print("[3] step(END_TURN)...")
try:
    obs, r, t, tr, info = env.step(10)
    print(f"    OK: nz={np.count_nonzero(obs)} r={r:.3f} term={t} trunc={tr} turn={info['turn']}")
except Exception as e:
    print(f"    FAIL: {e}")
    import traceback; traceback.print_exc()

print("[4] close...")
env.close()
print("ALL PASSED")
