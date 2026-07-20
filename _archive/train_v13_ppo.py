#!/usr/bin/env python3
"""VCMI-v13 MaskablePPO — pi=[256,256] vf=[256,256] 独立双网络"""
import os, sys, time
import gymnasium as gym
from stable_baselines3.common.callbacks import BaseCallback

WS = "/home/administrator/vcmi-workspace"
os.environ["LD_LIBRARY_PATH"] = f"{WS}/vcmi/rel/bin:{WS}/vcmi_gym/connectors/rel"
os.environ["NO_WANDB"] = "true"

sys.path.insert(0, WS)
from vcmi_gym.envs.v13.vcmi_env import VcmiEnv as V13Env
gym.register(id="VCMI-v13", entry_point="vcmi_gym.envs.v13.vcmi_env:VcmiEnv",
             disable_env_checker=True, order_enforce=False)

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy

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
    return env.get_action_mask()

class LogCallback(BaseCallback):
    def __init__(self, save_dir, save_freq=5000):
        super().__init__()
        self.save_dir = save_dir; self.save_freq = save_freq
        os.makedirs(save_dir, exist_ok=True)
        self.ep_start = 0
    def _on_step(self):
        if self.n_calls > 0 and self.n_calls % self.save_freq == 0:
            self.model.save(os.path.join(self.save_dir, f"v13_{self.n_calls}_steps"))
        return True
    def _on_rollout_end(self):
        log = self.model.logger.name_to_value
        rew = log.get("rollout/ep_rew_mean", 0)
        win = log.get("rollout/success_rate", 0)
        loss = log.get("train/loss", 0)
        clip = log.get("train/clip_fraction", 0)
        ev = log.get("train/explained_variance", -1)
        fps = log.get("time/fps", 0)
        steps = log.get("time/total_timesteps", 0)
        print(f"[{int(steps):5d}] rew={rew:6.0f} win={win:.2f} loss={loss:.0f} clip={clip:.3f} ev={ev:.3f} fps={fps:.0f}")
    def _on_training_end(self):
        self.model.save(os.path.join(self.save_dir, "final_model"))

# 独立双网络
# --- 环境变量配置 ---
MAP_NAME = os.environ.get("VCMI_MAP", "gym/A1.vmap")
TOTAL_STEPS = int(os.environ.get("VCMI_STEPS", "50000"))
DEVICE = os.environ.get("VCMI_DEVICE", "cpu")

policy_kwargs = dict(net_arch=dict(pi=[256, 256], vf=[256, 256]))

print(f"VCMI-v13 PPO pi=[256,256] vf=[256,256] n_steps=1024 n_epochs=15")
print(f"  map={MAP_NAME} steps={TOTAL_STEPS} device={DEVICE}")
env = gym.make("VCMI-v13", mapname=MAP_NAME,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    max_steps=200, allow_retreat=False)
env = FlattenV13Obs(env)
env = ActionMasker(env, mask_fn)

# --- 模型续训 ---
MODEL_DIR = f"{WS}/models/v13_ppo"
final_model = os.path.join(MODEL_DIR, "final_model.zip")
if os.path.exists(final_model):
    print(f"  Loading existing model: {final_model}")
    model = MaskablePPO.load(final_model, env=env, device=DEVICE)
else:
    print("  No existing model, initializing new")
    model = MaskablePPO(MaskableActorCriticPolicy, env,
        policy_kwargs=policy_kwargs,
        learning_rate=3e-4, n_steps=1024, batch_size=64, n_epochs=15,
        gamma=0.99, gae_lambda=0.95, clip_range=0.2,
        ent_coef=0.01, vf_coef=0.5, max_grad_norm=0.5,
        device=DEVICE, verbose=1)

t0 = time.time()
model.learn(total_timesteps=TOTAL_STEPS, callback=LogCallback(MODEL_DIR, 5000))

from stable_baselines3.common.logger import Logger
import numpy as np
log = model.logger.name_to_value
ev, cf = log.get("train/explained_variance",-1), log.get("train/clip_fraction",-1)
vl, sr = log.get("train/value_loss",-1), log.get("rollout/success_rate",-1)
print(f"Done {time.time()-t0:.0f}s | ev={ev:.4f} clip={cf:.4f} vloss={vl:.0f} win={sr:.2f}")
import os as _os; _os._exit(0)
