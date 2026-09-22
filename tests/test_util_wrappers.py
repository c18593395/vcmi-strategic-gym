"""Engine-free unit tests for envs/util/wrappers.py.

The `envs/v13+/test_*.py` scripts need `libmlclient.so` plus a live VCMI server,
so they cannot run in CI. These tests cover the pure-Python wrapper logic
against a stub environment (gymnasium + numpy only).

Run: python -m unittest discover -s tests -v
"""

import unittest

import gymnasium as gym
import numpy as np

from envs.util.wrappers import (
    BlankObservationSpaceWrapper,
    LegacyActionSpaceWrapper,
    LegacyObservationSpaceWrapper,
)


class StubEnv(gym.Env):
    """Minimal stand-in for the dict-observation / action-mask env contract."""

    def __init__(self, n_actions=5, obs_dim=3):
        self.action_space = gym.spaces.Discrete(n_actions)
        self.observation_space = gym.spaces.Dict({
            "observation": gym.spaces.Box(-1.0, 1.0, shape=(obs_dim,), dtype=np.float32),
            "action_mask": gym.spaces.MultiBinary(n_actions),
            "links": gym.spaces.Box(0.0, 1.0, shape=(obs_dim,), dtype=np.float32),
        })
        self.seen_actions = []
        self._last = None

    def _obs(self):
        n = self.action_space.n
        return {
            "observation": np.arange(3, dtype=np.float32),
            "action_mask": np.array([True] * (n - 1) + [False]),
            "links": np.arange(3, dtype=np.float32) + 10,
        }

    def reset(self, **kwargs):
        self._last = self._obs()
        return self._last, {"reset": True}

    def step(self, action):
        self.seen_actions.append(action)
        self._last = self._obs()
        return self._last, 1.0, False, False, {"action": action}

    # provided by LegacyObservationSpaceWrapper in the real env chain
    def action_mask(self):
        return self._last["action_mask"]

    def links(self):
        return self._last["links"]


class TestLegacyActionSpaceWrapper(unittest.TestCase):
    def test_action_space_is_shifted_by_one(self):
        env = LegacyActionSpaceWrapper(StubEnv(n_actions=5))
        self.assertEqual(env.action_space.n, 4)

    def test_action_mask_drops_first_entry(self):
        stub = StubEnv(n_actions=5)
        env = LegacyActionSpaceWrapper(stub)
        stub.reset()
        self.assertEqual(list(env.action_mask()), [True, True, True, False])

    def test_step_forwards_action_plus_one(self):
        stub = StubEnv(n_actions=5)
        env = LegacyActionSpaceWrapper(stub)
        env.step(0)
        env.step(3)
        self.assertEqual(stub.seen_actions, [1, 4])


class TestLegacyObservationSpaceWrapper(unittest.TestCase):
    def test_observation_space_is_inner_box(self):
        stub = StubEnv()
        env = LegacyObservationSpaceWrapper(stub)
        self.assertEqual(env.observation_space, stub.observation_space["observation"])

    def test_reset_returns_plain_observation(self):
        env = LegacyObservationSpaceWrapper(StubEnv())
        obs, info = env.reset()
        self.assertIsInstance(obs, np.ndarray)
        self.assertEqual(obs.shape, (3,))
        self.assertEqual(info, {"reset": True})

    def test_step_returns_five_tuple(self):
        env = LegacyObservationSpaceWrapper(StubEnv())
        env.reset()
        out = env.step(2)
        self.assertEqual(len(out), 5)
        self.assertEqual(out[1], 1.0)

    def test_action_mask_and_links_expose_last_dict_obs(self):
        env = LegacyObservationSpaceWrapper(StubEnv())
        env.reset()
        self.assertEqual(list(env.action_mask()), [True, True, True, True, False])
        self.assertEqual(list(env.links()), [10.0, 11.0, 12.0])

    def test_composed_chain_matches_real_usage(self):
        stub = StubEnv(n_actions=5)
        env = LegacyActionSpaceWrapper(LegacyObservationSpaceWrapper(stub))
        self.assertEqual(env.action_space.n, 4)
        env.reset()
        self.assertEqual(list(env.action_mask()), [True, True, True, False])


class TestBlankObservationSpaceWrapper(unittest.TestCase):
    def test_space_is_single_element_box(self):
        env = BlankObservationSpaceWrapper(StubEnv())
        self.assertEqual(env.observation_space.shape, (1,))

    def test_reset_and_step_return_empty_obs(self):
        env = BlankObservationSpaceWrapper(StubEnv())
        obs, _info = env.reset()
        self.assertEqual(obs.shape, (1,))
        self.assertEqual(env.step(0)[0].shape, (1,))

    def test_graph_obs_delegates_to_env_obs(self):
        stub = StubEnv()
        stub.obs = "GRAPH"
        env = BlankObservationSpaceWrapper(stub)
        self.assertEqual(env.graph_obs(), "GRAPH")


if __name__ == "__main__":
    unittest.main()
