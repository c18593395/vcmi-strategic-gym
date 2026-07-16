#!/usr/bin/env python3
"""test_strategic_env.py — StrategicEnv 端到端验证"""

import sys, os, time, subprocess

# Kill any leftover VCMI
subprocess.run(["pkill", "-f", "vcmi"], capture_output=True)
time.sleep(1)

os.environ.setdefault("LD_LIBRARY_PATH",
    "/home/administrator/vcmi-workspace/vcmi/rel/bin:"
    "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel")
sys.path.insert(0, "/home/administrator/vcmi-workspace")
sys.path.insert(0, "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel")

print("=" * 60)
print("StrategicEnv E2E Test")
print("=" * 60)

from vcmi_gym.envs.v13.strategic_env import StrategicEnv

print("\n[1] Creating env (s1.vmap)...")
env = StrategicEnv(
    mapname="s1.vmap",
    red="StupidAI",
    blue="StupidAI",
    boot_timeout=30,
    random_heroes=0,
    vcmienv_loglevel="WARN",
    vcmi_loglevel_global="error",
    vcmi_loglevel_ai="error",
    reward_step_fixed=-0.1,
)
print(f"  Env: {type(env).__name__}")
print(f"  Action space: {env.action_space}")
print(f"  Observation space: {env.observation_space}")

print("\n[2] reset()...")
sys.stdout.flush()
t0 = time.time()
obs, info = env.reset()
elapsed = time.time() - t0
print(f"  obs shape: {obs.shape}")
print(f"  obs[:24]: {obs[:24]}")
print(f"  info: {info}")
print(f"  time: {elapsed:.1f}s")
sys.stdout.flush()

print(f"\n[3] Running {env.max_turns} steps...")
sys.stdout.flush()
total_reward = 0.0
for i in range(env.max_turns):
    action = env.random_action()
    t0 = time.time()
    obs, reward, terminated, truncated, info = env.step(action)
    elapsed = time.time() - t0
    total_reward += reward
    print(f"  Step {i+1}: act={action} rew={reward:.2f} "
          f"tot={total_reward:.2f} done={terminated or truncated} "
          f"({elapsed:.1f}s)", flush=True)
    if terminated or truncated:
        print(f"  Episode finished early", flush=True)
        break

print(f"\n[4] Final stats:")
print(f"  Steps: {i+1}")
print(f"  Total reward: {total_reward:.2f}")
print(f"  Terminated: {terminated}  Truncated: {truncated}")
print(f"  Info: {info}")

print(f"\n[5] render():")
print(env.render())

print(f"\n{'=' * 60}")
if i >= 0:
    print("** TEST PASSED **")
else:
    print("** TEST FAILED **")
