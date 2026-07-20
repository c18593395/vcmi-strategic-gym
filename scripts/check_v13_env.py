"""Quick check: v13 battle env import + reset"""
import sys, os
sys.path.insert(0, "/home/administrator/vcmi-workspace")
os.environ["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-workspace/vcmi/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"

import gymnasium as gym
from vcmi_gym.envs.v13.vcmi_env import VcmiEnv as V13Env

gym.register(id="VCMI-v13", entry_point="vcmi_gym.envs.v13.vcmi_env:VcmiEnv",
             disable_env_checker=True, order_enforce=False)

print("Creating env...")
sys.stdout.flush()
env = gym.make("VCMI-v13", mapname="gym/A1.vmap")
print("Reset...")
sys.stdout.flush()
obs, info = env.reset()
print(f"obs['observation']: {obs['observation'].shape}")
print(f"obs['action_mask']: {obs['action_mask'].shape} sum={obs['action_mask'].sum()}")
env.close()
print("V13 battle env: OK")
