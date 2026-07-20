#!/usr/bin/env python3
"""Phase B Strategic Training — MaskablePPO on FakeStrategicEnv

Starts training on the fake env to validate the full pipeline:
  env → wrapper → ActionMasker → MaskablePPO → checkpoint → eval

Usage:
  python strategic_train.py
"""
import os, sys, time
import gymnasium as gym
import numpy as np

from stable_baselines3.common.callbacks import BaseCallback, EvalCallback

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy

# Make sure the envs are registered (strategic_env.py runs gym.register() at import)
import strategic_env  # noqa: F401


# ============================
# Wrappers
# ============================

class FakeStrategicWrapper(gym.Wrapper):
    """Add a dummy action mask to FakeStrategicEnv.

    The real StrategicEnv will provide action_mask in the observation dict,
    but FakeStrategicEnv returns a flat 200-dim observation. This wrapper
    injects a mask that allows all 11 actions for training pipeline testing.
    """

    def __init__(self, env):
        super().__init__(env)
        self._mask = np.ones(env.action_space.n, dtype=bool)

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self._mask[:] = True
        return obs, info

    def step(self, action):
        obs, rew, term, trunc, info = self.env.step(action)
        self._mask[:] = True
        return obs, rew, term, trunc, info

    def get_action_mask(self):
        return self._mask


def mask_fn(env):
    """ActionMasker-compatible mask function."""
    return env.get_action_mask()


# ============================
# Callbacks
# ============================

class LogCallback(BaseCallback):
    """Print rollout metrics after each rollout and save checkpoints."""

    def __init__(self, save_dir, save_freq=10000):
        super().__init__()
        self.save_dir = save_dir
        self.save_freq = save_freq
        os.makedirs(save_dir, exist_ok=True)

    def _on_step(self):
        if self.n_calls > 0 and self.n_calls % self.save_freq == 0:
            path = os.path.join(self.save_dir, f"strategic_{self.n_calls}_steps")
            self.model.save(path)
            print(f"  >>> Checkpoint saved: {path}")
        return True

    def _on_rollout_end(self):
        log = self.model.logger.name_to_value
        rew = log.get("rollout/ep_rew_mean", 0.0)
        loss = log.get("train/loss", 0.0)
        clip = log.get("train/clip_fraction", 0.0)
        ev = log.get("train/explained_variance", -1.0)
        fps = log.get("time/fps", 0.0)
        steps = log.get("time/total_timesteps", 0)
        print(
            f"[{int(steps):5d}] rew={rew:7.2f}  "
            f"loss={loss:.0f}  clip={clip:.3f}  "
            f"ev={ev:.3f}  fps={fps:.0f}"
        )

    def _on_training_end(self):
        path = os.path.join(self.save_dir, "strategic_final")
        self.model.save(path)
        print(f"  >>> Final model saved: {path}")


# ============================
# Config
# ============================

TOTAL_TIMESTEPS = 100_000
EVAL_INTERVAL = 10_000       # every N steps → run eval
EVAL_EPISODES = 10
SAVE_DIR = "models/strategic_ppo"
TENSORBOARD_LOG = "./logs/strategic/"
DEVICE = "cpu"

policy_kwargs = dict(
    net_arch=dict(pi=[512, 256], vf=[512, 256]),
)

print("=" * 60)
print("  VCMI Strategic Phase B — MaskablePPO on FakeStrategicEnv")
print("=" * 60)
print(f"  total_timesteps = {TOTAL_TIMESTEPS}")
print(f"  policy_arch     = 200 → [512, 256] → 11")
print(f"  n_steps         = 2048")
print(f"  batch_size      = 64")
print(f"  eval_interval   = {EVAL_INTERVAL} steps ({EVAL_EPISODES} episodes)")
print(f"  save_dir        = {SAVE_DIR}")
print(f"  tensorboard     = {TENSORBOARD_LOG}")
print(f"  device          = {DEVICE}")
print()

# ============================
# Environment
# ============================

env = gym.make("VCMI-strategic-fake-v1")
env = FakeStrategicWrapper(env)
env = ActionMasker(env, mask_fn)

eval_env = gym.make("VCMI-strategic-fake-v1")
eval_env = FakeStrategicWrapper(eval_env)
eval_env = ActionMasker(eval_env, mask_fn)

# ============================
# Model
# ============================

model = MaskablePPO(
    MaskableActorCriticPolicy,
    env,
    policy_kwargs=policy_kwargs,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    vf_coef=0.5,
    max_grad_norm=0.5,
    device=DEVICE,
    verbose=1,
    tensorboard_log=TENSORBOARD_LOG,
)

# ============================
# Callbacks
# ============================

eval_callback = EvalCallback(
    eval_env,
    best_model_save_path=os.path.join(SAVE_DIR, "best"),
    log_path=os.path.join(SAVE_DIR, "eval"),
    eval_freq=EVAL_INTERVAL,
    n_eval_episodes=EVAL_EPISODES,
    deterministic=True,
    render=False,
    verbose=1,
)

log_callback = LogCallback(SAVE_DIR, save_freq=EVAL_INTERVAL)

# ============================
# Train
# ============================

t0 = time.time()
model.learn(
    total_timesteps=TOTAL_TIMESTEPS,
    callback=[eval_callback, log_callback],
    tb_log_name="strategic",
)
elapsed = time.time() - t0

# ============================
# Summary
# ============================

log = model.logger.name_to_value
print()
print("=" * 60)
print("  Training complete")
print("=" * 60)
print(f"  elapsed          = {elapsed:.0f}s ({elapsed / 60:.1f} min)")
print(f"  total_timesteps  = {log.get('time/total_timesteps', '?'):>7}")
print(f"  ep_rew_mean      = {log.get('rollout/ep_rew_mean', 0.0):>7.2f}")
print(f"  ep_len_mean      = {log.get('rollout/ep_len_mean', 0.0):>7.1f}")
print(f"  loss             = {log.get('train/loss', 0.0):>7.0f}")
print(f"  clip_fraction    = {log.get('train/clip_fraction', 0.0):>7.3f}")
print(f"  explained_var    = {log.get('train/explained_variance', 0.0):>7.3f}")
print(f"  fps              = {log.get('time/fps', 0.0):>7.0f}")
print(f"  best model       = {SAVE_DIR}/best/best_model.zip")
print(f"  final model      = {SAVE_DIR}/strategic_final.zip")
print()
