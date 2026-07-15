"""
VCMI 战略 Gym 环境 — 冒险地图 RL 训练
Phase B: strategic_env.py

观测 ~200 维：英雄位置/兵力/移动力、城镇/资源、敌方可见信息、日期
动作：移动(8) + 交互 + 城镇 + 全局
奖励：占矿+5 捡宝+3 攻城+30 赢+200 Q键摆烂-2
"""
import gymnasium as gym
import numpy as np
import struct
import ctypes
import time
import threading
import os
from typing import Optional

# ------------------------------------------------------------
# 从 C 结构体读取状态
# ------------------------------------------------------------

class StrategicState:
    """从 g_strategic_state 读取游戏状态"""
    
    def __init__(self, lib_path="/home/administrator/vcmi-native/rel/bin/libmlclient.so"):
        self.lib = ctypes.CDLL(lib_path)
        self._size = 2048
    
    def read(self):
        """返回 dict：day/week/month, players[], heroes[], towns[]"""
        ptr = ctypes.c_void_p.in_dll(self.lib, "g_strategic_state")
        if not ptr.value:
            return None
        data = ctypes.string_at(ptr.value, self._size)
        
        state = {}
        off = 0
        
        # Global: day, week, month, current_player, map_w, map_h, underground, player_count
        fields = ["day", "week", "month", "current_player", "map_w", "map_h", "underground", "player_count"]
        for f in fields:
            state[f] = struct.unpack_from("i", data, off)[0]
            off += 4
        
        # Players (8 max, each 56 bytes: color, human, 7 resources, hero_count, town_count, alive)
        state["players"] = []
        for _ in range(state["player_count"]):
            p = {}
            vals = struct.unpack_from("iiiiiiiii", data, off)  # color,human,gold,wood,mercury,ore,sulfur,crystal,gems
            p["color"] = vals[0]; p["human"] = vals[1]
            p["gold"] = vals[2]; p["wood"] = vals[3]; p["mercury"] = vals[4]
            p["ore"] = vals[5]; p["sulfur"] = vals[6]; p["crystal"] = vals[7]; p["gems"] = vals[8]
            off += 36  # 9*4
            vals2 = struct.unpack_from("iii", data, off)
            p["hero_count"] = vals2[0]; p["town_count"] = vals2[1]; p["alive"] = vals2[2]
            off += 12 + 8  # 3*4 + padding
            state["players"].append(p)
        
        # Heroes (8 max, each ~120 bytes)
        state["heroes"] = []
        # Simplified: just read first few fields
        off = 32 + 8 * 56  # After global + 8 player slots
        for _ in range(8):
            vals = struct.unpack_from("iiiiiiiiiii", data, off)
            if vals[0] == -1:  # sentinel
                break
            h = {"id": vals[0], "owner": vals[1], "x": vals[2], "y": vals[3], "z": vals[4],
                 "movement": vals[5], "max_movement": vals[6], "level": vals[7],
                 "attack": vals[8], "defense": vals[9], "power": vals[10]}
            state["heroes"].append(h)
            off += 128  # rough hero struct size
        
        # Towns (8 max)
        state["towns"] = []
        
        return state


# ------------------------------------------------------------
# Gym 环境
# ------------------------------------------------------------

class StrategicEnv(gym.Env):
    """VCMI 冒险地图 Gym 环境"""
    
    metadata = {"render_modes": ["ansi"], "render_fps": 30}
    
    # 动作空间
    MOVE_RIGHT, MOVE_DOWN_RIGHT, MOVE_DOWN, MOVE_DOWN_LEFT = 0, 1, 2, 3
    MOVE_LEFT, MOVE_UP_LEFT, MOVE_UP, MOVE_UP_RIGHT = 4, 5, 6, 7
    INTERACT = 8        # 捡取/访问
    NEXT_HERO = 9       # 下一英雄
    END_TURN = 10       # 结束回合
    
    N_ACTIONS = 11
    
    # 观测维度
    OBS_DIM = 200
    
    def __init__(self, mapname="gym/s1.vmap", max_turns=28, seed=None):
        super().__init__()
        
        self.mapname = mapname
        self.max_turns = max_turns  # 28天 = 4周
        
        # 空间定义
        self.action_space = gym.spaces.Discrete(self.N_ACTIONS)
        self.observation_space = gym.spaces.Box(
            low=-1e6, high=1e6, shape=(self.OBS_DIM,), dtype=np.float32
        )
        
        # 状态
        self._turn = 0
        self._prev_gold = 0
        self._prev_towns = 0
        self._prev_heroes = 0
        self._state_reader = StrategicState()
        self._conn = None  # connector (延迟初始化)
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._turn = 0
        self._prev_gold = 0
        self._prev_towns = 0
        self._prev_heroes = 0
        
        # 启动 VCMI + 等待 yourTurn
        self._start_connector()
        self._conn.adventure_wait()
        
        obs = self._make_obs()
        return obs, {}
    
    def step(self, action):
        # 发送动作
        self._conn.adventure_act(action)
        
        # 等待下一帧
        self._conn.adventure_wait()
        
        obs = self._make_obs()
        reward = self._calc_reward()
        self._turn += 1
        
        done = self._turn >= self.max_turns
        info = {}
        
        return obs, reward, done, False, info
    
    def _start_connector(self):
        """延迟初始化 connector"""
        if self._conn is not None:
            return
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "connector_v13",
            "/home/administrator/vcmi-native/rel/bin/connector_v13_adventure.so"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        self._conn = mod.ThreadConnector(
            red="MMAI_USER", blue="StupidAI",
            mapname=self.mapname,
            maxlogs=500, bootTimeout=30, userTimeout=30,
            vcmi_loglevel_global="error",
        )
        
        def _run():
            self._conn.start()
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        time.sleep(3)  # 等 VCMI 初始化
    
    def _make_obs(self):
        """构建观测向量"""
        state = self._state_reader.read()
        if state is None:
            return np.zeros(self.OBS_DIM, dtype=np.float32)
        
        obs = []
        
        # Global: day/week/month
        obs.append(state["day"])
        obs.append(state["week"])
        obs.append(state["month"])
        obs.append(state["current_player"])
        
        # Players: 自己的资源 (player 0 = red)
        if state["players"]:
            p = state["players"][0]
            obs.extend([p["gold"], p["wood"], p["mercury"], p["ore"], p["sulfur"], p["crystal"], p["gems"]])
            obs.append(p["hero_count"])
            obs.append(p["town_count"])
        
        # Enemy resources (player 1 = blue)
        if len(state["players"]) > 1:
            p = state["players"][1]
            obs.extend([p["gold"], p["wood"], p["mercury"], p["ore"], p["sulfur"], p["crystal"], p["gems"]])
        
        # Heroes: first hero of ours
        our_heroes = [h for h in state["heroes"] if h["owner"] == 0]
        if our_heroes:
            h = our_heroes[0]
            obs.extend([h["x"], h["y"], h["movement"], h["attack"], h["defense"], h["power"], h["level"]])
        else:
            obs.extend([0]*7)
        
        # Pad to OBS_DIM
        while len(obs) < self.OBS_DIM:
            obs.append(0)
        obs = obs[:self.OBS_DIM]
        
        return np.array(obs, dtype=np.float32)
    
    def _calc_reward(self):
        """计算奖励"""
        state = self._state_reader.read()
        if state is None or not state["players"]:
            return 0
        
        p = state["players"][0]
        
        # 资源变化奖励
        gold_delta = p["gold"] - self._prev_gold
        town_delta = p["town_count"] - self._prev_towns
        hero_delta = p["hero_count"] - self._prev_heroes
        
        reward = gold_delta * 0.001  # 金币小幅奖励
        reward += town_delta * 30       # 新城大奖励
        reward += hero_delta * 10       # 新英雄奖励
        
        self._prev_gold = p["gold"]
        self._prev_towns = p["town_count"]
        self._prev_heroes = p["hero_count"]
        
        # 游戏结束
        if state.get("game_over", 0) == 1:
            reward += 200  # 赢
        
        return reward
    
    def close(self):
        pass


# ------------------------------------------------------------
# 注册
# ------------------------------------------------------------

gym.register(
    id="VCMI-strategic-v1",
    entry_point="strategic_env:StrategicEnv",
    disable_env_checker=True,
)
