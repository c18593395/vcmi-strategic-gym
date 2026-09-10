"""
T13.8 — 模型接入层
将外挂 AI 协议客户端与 PPO 模型连接
"""
import threading
import time
import numpy as np
from typing import Optional, Callable, List
from .protocol import VCMIProtocolClient
from .packs import (
    PlayerColor, ObjectInstanceID,
    MoveHero, EndTurn, RecruitCreatures,
    BattleAction, EActionType, BattleSide,
)


class ModelState:
    """AI 模型的状态缓存"""
    def __init__(self):
        self.turn = 0
        self.resources = {"gold": 0, "wood": 0, "ore": 0, "mercury": 0,
                          "sulfur": 0, "crystal": 0, "elixir": 0}
        self.towns = {}      # town_id -> {built, garrison, ...}
        self.heroes = {}     # hero_id -> {level, x, y, army, ...}
        self.objects = {}    # obj_id -> {type, x, y, ...}
        self.in_battle = False
        self.battle_id = 0

    def to_observation(self) -> np.ndarray:
        """将状态转为模型输入向量"""
        # 简化实现: 返回全零占位 (实际需要根据战略状态构建 3464 维)
        return np.zeros(3464, dtype=np.float32)


class ModelBridge:
    """
    模型接入层 — 连接协议客户端与 PPO 模型
    
    架构:
    VCMI Server ←TCP→ VCMIProtocolClient ←→ ModelBridge ←→ PPO Model
    
    工作流:
    1. 协议客户端接收服务器包 → 更新状态
    2. 模型根据状态生成动作
    3. 动作通过协议客户端发送
    4. 重复直到回合结束
    
    与现有训练栈的兼容:
    - 接口与 train_wsl2_ppo_v2.py 的 obs/action 空间一致
    - 动作空间 25 (0-24): 移动/交互/招兵/建城/结束回合等
    - obs 空间 3464 维
    """

    OBS_DIM = 3464
    N_ACTIONS = 25  # 0-24 有效

    # 动作映射
    ACTION_MAP = {
        0: ("move_north", lambda s: {"path": [(s.hero_x, s.hero_y + 1, s.hero_z)], "hid": s.hero_id}),
        1: ("move_northeast", lambda s: {"path": [(s.hero_x + 1, s.hero_y + 1, s.hero_z)], "hid": s.hero_id}),
        2: ("move_east", lambda s: {"path": [(s.hero_x + 1, s.hero_y, s.hero_z)], "hid": s.hero_id}),
        3: ("move_southeast", lambda s: {"path": [(s.hero_x + 1, s.hero_y - 1, s.hero_z)], "hid": s.hero_id}),
        4: ("move_south", lambda s: {"path": [(s.hero_x, s.hero_y - 1, s.hero_z)], "hid": s.hero_id}),
        5: ("move_southwest", lambda s: {"path": [(s.hero_x - 1, s.hero_y - 1, s.hero_z)], "hid": s.hero_id}),
        6: ("move_west", lambda s: {"path": [(s.hero_x - 1, s.hero_y, s.hero_z)], "hid": s.hero_id}),
        7: ("move_northwest", lambda s: {"path": [(s.hero_x - 1, s.hero_y + 1, s.hero_z)], "hid": s.hero_id}),
        8: ("interact", None),     # 拾取/对话/攻击 — 需要具体对象
        9: ("next_hero", None),    # 切换英雄
        10: ("end_turn", None),
        11: ("recruit", None),     # 招兵
        12: ("build", None),       # 建城
        13: ("upgrade", None),     # 升级
        14: ("upgrade_town", None),
        15: ("disband", None),     # 解散
        16: ("exchange", None),    # 交换
        17: ("buy", None),         # 购买
        18: ("sell", None),        # 出售
        19: ("cast_spell", None),  # 施法
        20: ("hire_hero", None),   # 雇佣英雄
        21: ("set_formation", None),
        22: ("discharge_artifact", None),
        23: ("teleport_hero", None),
        24: ("wait", None),        # 等待
    }

    def __init__(self, client: VCMIProtocolClient, model=None):
        self.client = client
        self.model = model  # PPO model (torch.nn.Module or callable)
        self.state = ModelState()
        self.hero_id = 0
        self.hero_x = 0
        self.hero_y = 0
        self.hero_z = 0
        self.steps_in_turn = 0
        self.max_steps_per_turn = 200

        # 注册回调
        client.on_turn_start = self._on_turn_start
        client.on_turn_end = self._on_turn_end
        client.on_new_turn = self._on_new_turn
        client.on_battle_start = self._on_battle_start
        client.on_battle_result = self._on_battle_result
        client.on_system_message = self._on_system_message

    def step(self) -> dict:
        """
        执行一步 AI 决策
        返回 {observation, action, reward, done, info}
        """
        # 1. 构建观测
        obs = self._build_observation()

        # 2. 模型决策
        action = self._decide_action(obs)

        # 3. 执行动作
        result = self._execute_action(action)

        return {
            "observation": obs,
            "action": action,
            "reward": result.get("reward", 0.0),
            "done": result.get("done", False),
            "info": result,
        }

    def _decide_action(self, obs: np.ndarray) -> int:
        """模型决策"""
        if self.model is None:
            # 无模型: 默认结束回合
            return 10  # end_turn

        # 模型推理
        with torch.no_grad():
            # obs shape: (OBS_DIM,) → (1, OBS_DIM)
            obs_t = torch.from_numpy(obs).unsqueeze(0).float()
            actions, values = self.model(obs_t)
            action = actions.argmax(dim=-1).item()

        return action

    def _execute_action(self, action: int) -> dict:
        """执行动作"""
        self.steps_in_turn += 1
        result = {"reward": 0.0, "done": False}

        name, fn = self.ACTION_MAP.get(action, ("unknown", None))

        if action == 10:  # end_turn
            self.client.send_end_turn()
            result["done"] = True
            result["reward"] = 100.0  # 结束回合奖励
        elif action <= 7:  # 移动
            if fn:
                path_info = fn(self)
                self.client.send_move_hero(path_info["path"], path_info["hid"])
                result["reward"] = 1.0
        elif action == 11:  # 招兵
            if self._can_recruit():
                self._do_recruit()
                result["reward"] = 10.0
        elif action == 12:  # 建城
            if self._can_build():
                self._do_build()
                result["reward"] = 5.0
        elif action == 8:  # 交互
            result["reward"] = 2.0
        elif action == 24:  # 等待
            result["reward"] = 0.5
        else:
            # 其他动作: 简化处理
            result["reward"] = 0.0

        # 超时保护
        if self.steps_in_turn >= self.max_steps_per_turn:
            self.client.send_end_turn()
            result["done"] = True
            result["reward"] += 50.0

        return result

    def _build_observation(self) -> np.ndarray:
        """构建观测向量"""
        return self.state.to_observation()

    def _can_recruit(self) -> bool:
        """判断是否可以招兵"""
        return False  # 需要状态查询

    def _do_recruit(self):
        """执行招兵"""
        # 需要城镇/英雄信息
        pass

    def _can_build(self) -> bool:
        """判断是否可以建城"""
        return False

    def _do_build(self):
        """执行建城"""
        pass

    # ============================================================
    # 回调处理
    # ============================================================

    def _on_turn_start(self, data: dict):
        self.steps_in_turn = 0
        print(f"[MODEL] 回合开始 (player={data.get('player', '?')})")

    def _on_turn_end(self, data: dict):
        print(f"[MODEL] 回合结束")

    def _on_new_turn(self, data: dict):
        self.state.turn = data.get("turn", 0)
        print(f"[MODEL] 新回合: {self.state.turn}")

    def _on_battle_start(self, data: dict):
        self.state.in_battle = True
        self.state.battle_id = data.get("bid", 0)
        print(f"[MODEL] 战斗开始 (bid={data.get('bid', 0)})")

    def _on_battle_result(self, data: dict):
        self.state.in_battle = False
        winner = data.get("winner", -1)
        reward = 50.0 if winner == 0 else -50.0
        print(f"[MODEL] 战斗结束 (winner={winner}, reward={reward})")

    def _on_system_message(self, data: dict):
        msg = data.get("message", "")
        if msg:
            print(f"[MODEL] 消息: {msg}")

    # ============================================================
    # 启动/停止
    # ============================================================

    def run(self, max_turns: int = 1000):
        """主循环"""
        turn = 0
        while turn < max_turns and self.client.conn.connected:
            result = self.step()
            if result["done"]:
                turn += 1
                print(f"[MODEL] 回合 {turn} 完成 (reward={result['reward']:.1f})")
            time.sleep(0.01)  # 防止过快的请求

    def get_stats(self) -> dict:
        return {
            "turn": self.state.turn,
            "steps_in_turn": self.steps_in_turn,
            "in_battle": self.state.in_battle,
            "client_stats": self.client.get_stats(),
        }


# torch 导入 (可选)
try:
    import torch
except ImportError:
    torch = None
