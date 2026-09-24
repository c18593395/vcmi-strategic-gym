#!/usr/bin/env python3
"""
课程学习管理器
Curriculum Learning Manager

管理 Level 0-5 的课程学习，包括：
1. 地图池管理
2. 晋级条件检查
3. 训练状态保存/加载
4. 动态难度调整
"""

import json
import os
import yaml
from collections import deque
from datetime import datetime

class CurriculumManager:
    """课程学习管理器"""
    
    def __init__(self, config_path="curriculum_config.yaml"):
        """初始化课程学习管理器"""
        self.config_path = config_path
        self.config = self._load_config()
        self.state_path = self.config["output"]["curriculum_state_path"]
        
        # 状态
        self.current_level = 0
        self.episode_count = 0
        self.total_episodes = 0
        self.metrics_history = deque(maxlen=1000)
        self.level_history = []
        
        # 加载状态
        self._load_state()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """默认配置"""
        return {
            "curriculum": {
                "enabled": True,
                "start_level": 0,
                "max_level": 5,
                "episodes_per_level": 1000,
                "max_extension": 2000,
                "check_interval": 100,
                "promotion_window": 100
            },
            # 09-23 测试套件 M1 修复: 补 monitoring 段 — record_episode 直接取
            # self.config["monitoring"]["checkpoint_interval"], 原默认 config 无该段 →
            # yaml 加载失败走默认配置后 record_episode 抛 KeyError。值与 curriculum_config.yaml 一致。
            "monitoring": {
                "checkpoint_interval": 100,
                "log_interval": 10,
            },
            "output": {
                "curriculum_state_path": "/mnt/d/Bigdata/hero3_fresh/curriculum_state.json"
            }
        }
    
    def _load_state(self):
        """加载课程学习状态"""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r') as f:
                    state = json.load(f)
                    self.current_level = state.get("current_level", 0)
                    self.episode_count = state.get("episode_count", 0)
                    self.total_episodes = state.get("total_episodes", 0)
                    self.metrics_history = deque(state.get("metrics_history", []), maxlen=1000)
                    self.level_history = state.get("level_history", [])
                    print(f"Loaded curriculum state: Level {self.current_level}, Episode {self.episode_count}")
            except Exception as e:
                print(f"Error loading state: {e}")
    
    def _save_state(self):
        """保存课程学习状态"""
        state = {
            "current_level": self.current_level,
            "episode_count": self.episode_count,
            "total_episodes": self.total_episodes,
            "metrics_history": list(self.metrics_history),
            "level_history": self.level_history,
            "last_updated": datetime.now().isoformat()
        }
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def get_current_level_config(self):
        """获取当前 Level 配置"""
        level_key = f"level_{self.current_level}"
        if level_key in self.config:
            return self.config[level_key]
        return None
    
    def get_current_maps(self):
        """获取当前 Level 的地图列表"""
        level_config = self.get_current_level_config()
        if level_config:
            return level_config.get("maps", [])
        return []
    
    def get_training_params(self):
        """获取当前 Level 的训练参数"""
        level_config = self.get_current_level_config()
        if level_config:
            return level_config.get("training_params", {})
        return {}
    
    def record_episode(self, metrics):
        """记录一个 episode 的指标"""
        self.episode_count += 1
        self.total_episodes += 1
        
        # 添加元信息
        metrics["level"] = self.current_level
        metrics["episode"] = self.episode_count
        metrics["total_episode"] = self.total_episodes
        metrics["timestamp"] = datetime.now().isoformat()
        
        # 记录到历史
        self.metrics_history.append(metrics)
        
        # 定期保存
        # 09-23 测试套件 M1 修复: 防御式取值 — 兼容 monitoring 段或 checkpoint_interval 键缺失
        # (默认 config 已补齐该段, 此处再兜底一次防自定义 yaml 缺键)
        _ckpt_interval = self.config.get("monitoring", {}).get("checkpoint_interval", 100)
        if _ckpt_interval and self.episode_count % _ckpt_interval == 0:
            self._save_state()
        
        return metrics
    
    def check_promotion(self):
        """检查是否满足晋级条件"""
        if not self.config["curriculum"]["enabled"]:
            return False
        
        # 检查是否达到最小 episodes
        level_config = self.get_current_level_config()
        if not level_config:
            return False
        
        promotion_threshold = level_config.get("promotion_threshold", {})
        min_episodes = promotion_threshold.get("min_episodes", 100)
        
        if self.episode_count < min_episodes:
            return False
        
        # 获取最近 window 个 episodes 的指标
        window = self.config["curriculum"]["promotion_window"]
        recent_metrics = list(self.metrics_history)[-window:]
        
        if len(recent_metrics) < window:
            return False
        
        # 计算指标
        positive_reward_rate = sum(1 for m in recent_metrics if m.get("reward", 0) > 0) / len(recent_metrics)
        average_reward = sum(m.get("reward", 0) for m in recent_metrics) / len(recent_metrics)
        
        # 检查晋级条件
        if "positive_reward_rate" in promotion_threshold:
            if positive_reward_rate < promotion_threshold["positive_reward_rate"]:
                return False
        
        if "average_reward" in promotion_threshold:
            if average_reward < promotion_threshold["average_reward"]:
                return False
        
        if "win_rate" in promotion_threshold:
            # 计算胜率 (需要额外的胜率数据)
            win_rate = sum(1 for m in recent_metrics if m.get("win", False)) / len(recent_metrics)
            if win_rate < promotion_threshold["win_rate"]:
                return False
        
        return True
    
    def promote_to_next_level(self):
        """晋级到下一个 Level"""
        if self.current_level >= self.config["curriculum"]["max_level"]:
            print(f"Already at max level {self.current_level}, cannot promote")
            return False
        
        # 记录晋级历史
        self.level_history.append({
            "from_level": self.current_level,
            "to_level": self.current_level + 1,
            "episode_count": self.episode_count,
            "total_episodes": self.total_episodes,
            "timestamp": datetime.now().isoformat()
        })
        
        # 晋级
        self.current_level += 1
        self.episode_count = 0
        
        # 保存状态
        self._save_state()
        
        print(f"Promoted to Level {self.current_level}")
        return True
    
    def should_extend_training(self):
        """检查是否应该延长训练"""
        level_config = self.get_current_level_config()
        if not level_config:
            return False
        
        max_episodes = level_config.get("episodes", 1000)
        max_extension = self.config["curriculum"]["max_extension"]
        
        # 如果已经超过最大延长，不再延长
        if self.episode_count >= max_episodes + max_extension:
            return False
        
        # 如果已经超过基础 episodes，但还没满足晋级条件，延长
        if self.episode_count >= max_episodes and not self.check_promotion():
            return True
        
        return False
    
    def get_status(self):
        """获取课程学习状态"""
        level_config = self.get_current_level_config()
        maps = self.get_current_maps()
        
        # 计算最近指标
        recent_metrics = list(self.metrics_history)[-100:]
        if recent_metrics:
            positive_reward_rate = sum(1 for m in recent_metrics if m.get("reward", 0) > 0) / len(recent_metrics)
            average_reward = sum(m.get("reward", 0) for m in recent_metrics) / len(recent_metrics)
        else:
            positive_reward_rate = 0
            average_reward = 0
        
        return {
            "current_level": self.current_level,
            "level_name": level_config.get("name", "") if level_config else "",
            "episode_count": self.episode_count,
            "total_episodes": self.total_episodes,
            "maps_count": len(maps),
            "positive_reward_rate": positive_reward_rate,
            "average_reward": average_reward,
            "can_promote": self.check_promotion(),
            "should_extend": self.should_extend_training(),
            "level_history": self.level_history
        }
    
    def print_status(self):
        """打印课程学习状态"""
        status = self.get_status()
        
        print("="*70)
        print("课程学习状态")
        print("="*70)
        print(f"当前 Level: {status['current_level']}")
        print(f"Level 名称: {status['level_name']}")
        print(f"当前 Level Episodes: {status['episode_count']}")
        print(f"总 Episodes: {status['total_episodes']}")
        print(f"地图数量: {status['maps_count']}")
        print(f"正奖励率: {status['positive_reward_rate']:.2%}")
        print(f"平均奖励: {status['average_reward']:.2f}")
        print(f"可以晋级: {'是' if status['can_promote'] else '否'}")
        print(f"需要延长: {'是' if status['should_extend'] else '否'}")
        print("="*70)
        
        if status['level_history']:
            print("\n晋级历史:")
            for h in status['level_history']:
                print(f"  Level {h['from_level']} -> {h['to_level']} at episode {h['episode_count']}")

def main():
    """主函数"""
    manager = CurriculumManager()
    manager.print_status()

if __name__ == "__main__":
    main()
