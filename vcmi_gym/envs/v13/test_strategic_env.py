#!/usr/bin/env python3
"""test_strategic_env.py — StrategicEnv 端到端验证脚本"""

import sys
import os
import time

# ---- WSL2 路径设置 ----
VCMI_REL = "/home/administrator/vcmi-workspace/vcmi/rel/bin"
CONN_REL = "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
VCMI_GYM = "/home/administrator/vcmi-workspace/vcmi_gym"
VENV_PYTHON = "/home/administrator/vcmi-workspace/venv/bin/python"

os.environ.setdefault("LD_LIBRARY_PATH", f"{VCMI_REL}:{CONN_REL}")
sys.path.insert(0, VCMI_GYM)
sys.path.insert(0, CONN_REL)

# ---- 测试 StrategicEnv ----
print("=" * 60)
print("StrategicEnv 验证测试")
print("=" * 60)

# 先确保 VCMI 没有之前的进程残留
import subprocess
subprocess.run(["pkill", "-f", "vcmi"], capture_output=True)
time.sleep(1)

from vcmi_gym.envs.v13.strategic_env import StrategicEnv

print("\n[1] 创建环境 (map=s1.vmap)...")
env = StrategicEnv(
    mapname="s1.vmap",
    seed=42,
    max_turns=5,
    random_heroes=0,
    boot_timeout=120,
    vcmi_loglevel_global="warn",
    vcmi_loglevel_ai="warn",
    vcmienv_loglevel="INFO",
    red="MMAI_USER",
    blue="StupidAI",
)
print(f"  env: {env}")
print(f"  action_space: {env.action_space}")
print(f"  observation_space: {env.observation_space}")

print("\n[2] reset()...")
t0 = time.time()
obs, info = env.reset()
elapsed = time.time() - t0
print(f"  obs shape: {obs.shape}")
print(f"  obs[:20]: {obs[:20]}")
print(f"  info: {info}")
print(f"  reset time: {elapsed:.1f}s")

print(f"\n[3] 运行 {env.max_turns} 步循环...")
total_reward = 0.0
for i in range(env.max_turns):
    t0 = time.time()
    action = env.random_action()
    obs, reward, terminated, truncated, info = env.step(action)
    elapsed = time.time() - t0
    total_reward += reward
    print(f"  Step {i+1}: action={action} reward={reward:.2f} "
          f"total={total_reward:.2f} done={terminated or truncated} "
          f"({elapsed:.1f}s)")

print(f"\n[4] 验证结果:")
print(f"  总步数: {i+1}")
print(f"  总奖励: {total_reward:.2f}")
print(f"  终止:  terminated={terminated} truncated={truncated}")
print(f"  最终 info: {info}")

print(f"\n[5] render():")
print(env.render())

print(f"\n[6] close()...")
env.close()

print(f"\n{'=' * 60}")
if i >= env.max_turns - 1:
    print("** TEST PASSED **")
    sys.exit(0)
else:
    print("** TEST FAILED ** (unexpected early termination)")
    sys.exit(1)
