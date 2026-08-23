import sys, os
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["PYTHONPATH"] = "/mnt/d/Bigdata/hero3_fresh"

import numpy as np
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

env = StrategicEnv(mapname='T01_adventure_20X20_01.vmap', max_turns=5, seed=42)
obs, info = env.reset()

# Direct call to _build_terrain_grid
state = env._read_state()
tg_direct = env._build_terrain_grid(state)
print(f"Direct call: shape={tg_direct.shape} range=[{tg_direct.min():.4f}, {tg_direct.max():.4f}] nonz={np.count_nonzero(tg_direct)}")

# Check info
tg_info = info.get("terrain_grid")
if tg_info is not None:
    print(f"Info: shape={tg_info.shape} range=[{tg_info.min():.4f}, {tg_info.max():.4f}] nonz={np.count_nonzero(tg_info)}")
else:
    print("Info: None")

# Check self._terrain_grid
print(f"Self: shape={env._terrain_grid.shape} range=[{env._terrain_grid.min():.4f}, {env._terrain_grid.max():.4f}] nonz={np.count_nonzero(env._terrain_grid)}")

env.close()
