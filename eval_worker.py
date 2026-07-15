import os as _os, sys, json, numpy as np
_os.environ["NO_WANDB"] = "true"
sys.path.insert(0, "/home/administrator/vcmi-workspace")
import gymnasium as gym
from vcmi_gym.envs.v13.vcmi_env import VcmiEnv
gym.register(id="VCMI-v13", entry_point="vcmi_gym.envs.v13.vcmi_env:VcmiEnv",
             disable_env_checker=True, order_enforce=False)
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker

class FlattenV13Obs(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.observation_space = env.observation_space["observation"]
        self._mask = None
    def reset(self, **kwargs):
        obs_dict, info = self.env.reset(**kwargs)
        self._mask = obs_dict["action_mask"]
        return obs_dict["observation"], info
    def step(self, action):
        obs_dict, rew, term, trunc, info = self.env.step(action)
        self._mask = obs_dict["action_mask"]
        return obs_dict["observation"], rew, term, trunc, info
    def get_action_mask(self):
        return self._mask

def mask_fn(env):
    return env.env.get_action_mask()

map_name = sys.argv[1]
n_episodes = int(sys.argv[2])
out_file = sys.argv[3]

MODEL = "/home/administrator/vcmi-workspace/models/v13_ppo/final_model.zip"
model = MaskablePPO.load(MODEL)
env = gym.make("VCMI-v13", mapname=map_name, vcmi_loglevel_global="error",
               max_steps=600, allow_retreat=False)
env = FlattenV13Obs(env)
env = ActionMasker(env, mask_fn)

wins = 0
rewards = []
lengths = []
for ep in range(n_episodes):
    obs, _ = env.reset()
    ep_rew, ep_len = 0, 0
    for step in range(600):
        mask = env.env.get_action_mask()
        action, _ = model.predict(obs, deterministic=True, action_masks=mask)
        obs, rew, term, trunc, _ = env.step(action)
        ep_rew += rew
        ep_len += 1
        if term or trunc:
            break
    wins += 1 if ep_rew > 0 else 0
    rewards.append(ep_rew)
    lengths.append(ep_len)

result = {
    "map": map_name,
    "games": n_episodes,
    "win_rate": wins / n_episodes,
    "avg_reward": float(np.mean(rewards)),
    "avg_len": float(np.mean(lengths)),
}
with open(out_file, "w") as f:
    json.dump(result, f)
ar = result["avg_reward"]
print("DONE: %s win=%d/%d avg_rew=%.0f" % (map_name, wins, n_episodes, ar), flush=True)
_os._exit(0)
