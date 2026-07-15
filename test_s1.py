import sys, time
sys.path.insert(0, ".")
import gymnasium as gym
from vcmi_gym.envs.v13.vcmi_env import VcmiEnv
gym.register(id="T", entry_point="vcmi_gym.envs.v13.vcmi_env:VcmiEnv",
             disable_env_checker=True, order_enforce=False)

print("Loading s1.vmap...")
t0 = time.time()
try:
    env = gym.make("T", mapname="gym/s1.vmap", max_steps=10,
                    vcmi_stats_mode="disabled", vcmi_loglevel_global="error",
                    user_timeout=10, boot_timeout=10)
    obs, info = env.reset()
    print("OK in %.1fs" % (time.time()-t0))
    env.close()
except Exception as e:
    print("FAIL in %.1fs: %s" % (time.time()-t0, e))
