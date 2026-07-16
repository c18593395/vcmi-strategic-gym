"""Test FakeStrategicEnv"""
import gymnasium as gym
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import strategic_env  # noqa: register envs

env = gym.make("VCMI-strategic-fake-v1", max_turns=5)
obs, info = env.reset()
print(f"reset obs: shape={obs.shape} sum={obs.sum():.1f}")

total_rew = 0
for i in range(5):
    a = env.action_space.sample()
    obs, rew, done, trunc, info = env.step(a)
    total_rew += rew
    print(f"  step {i}: action={a} reward={rew:.3f} done={done}")
print(f"total reward: {total_rew:.1f}")
env.close()
print("Fake env test: PASS")
