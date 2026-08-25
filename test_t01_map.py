import sys
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

mapname = "/mnt/d/Bigdata/hero3_fresh/Maps/training/T01_adventure_20X20_01.vmap"
print(f"Testing map: {mapname}")

try:
    env = StrategicEnv(
        mapname=mapname,
        max_turns=5,
        vcmi_loglevel_global="error",
        vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR",
        red="StupidAI",
        blue="StupidAI",
        random_heroes=1,
        boot_timeout=30,
        vcmi_timeout=60,
    )
    obs, _ = env.reset()
    print(f"Reset OK, obs shape: {obs.shape}")
    env.close()
    print("Test passed!")
except Exception as e:
    print(f"Error: {e}")
