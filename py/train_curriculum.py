#!/usr/bin/env python3
"""
课程学习训练脚本
Curriculum Learning Training Script

集成课程学习管理器，支持：
1. 自动晋级
2. 动态地图选择
3. 训练状态保存/加载
4. 监控指标记录
"""
import os

import subprocess, json, time, os, random, signal, sys
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical
import yaml

# 导入课程学习管理器
sys.path.insert(0, os.path.dirname(__file__))
from curriculum_manager import CurriculumManager

# === 训练参数 ===
BATCH = 128
STEPS_PER_EP = 50
LR = 1e-4
CLIP = 0.2
EPOCHS = 4
GAMMA = 0.99
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === 路径配置 ===
VENV = os.environ.get("VENV", "/home/administrator/vcmi-workspace/venv/bin/python")
RUNNER = os.environ.get("RUNNER", "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py")
TRAJ = "/tmp/traj_one.json"
MODEL_PATH = os.environ.get("MODEL_PATH", "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt")
STATE_PATH = os.environ.get("STATE_PATH", "/mnt/d/Bigdata/hero3_fresh/wsl2_train_state.pt")
CURRICULUM_CONFIG = os.environ.get("CURRICULUM_CONFIG", "/mnt/d/Bigdata/hero3_fresh/curriculum_config.yaml")  # === 网络定义 ===
class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(264, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.actor = nn.Linear(128, 11)
        self.critic = nn.Linear(128, 1)
    
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

# === 初始化 ===
model = Net().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=LR)

# 课程学习管理器
curriculum = CurriculumManager(CURRICULUM_CONFIG)

def is_clean():
    """检查模型参数是否含 NaN/Inf"""
    for p in model.parameters():
        if torch.isnan(p).any() or torch.isinf(p).any():
            return False
    return True

def save_train_state(path, step=0):
    """保存模型+优化器+step计数"""
    torch.save({
        "model": model.state_dict(),
        "optimizer": opt.state_dict(),
        "step": step,
    }, path)

def save_shutdown(*args):
    """SIGTERM/SIGINT 时保存"""
    print("\n  Shutdown, saving train state...", flush=True)
    ckpt = f"/mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_shutdown_ckpt.pt"
    save_train_state(ckpt, total_steps)
    curriculum._save_state()
    print(f"  Saved {ckpt}", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, save_shutdown)
signal.signal(signal.SIGINT, save_shutdown)

def run_episode(mapname):
    """运行一个 episode"""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    cmd = [VENV, RUNNER, str(STEPS_PER_EP), TRAJ, mapname]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    try:
        proc.wait(timeout=STEPS_PER_EP*3 + 15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    try:
        with open(TRAJ) as f:
            d = json.load(f)
            if d.get("steps", 0) > 0 and not d.get("error"):
                return d
    except:
        pass
    return None

def collect_trajectories(maps, n_episodes):
    """收集轨迹数据"""
    batch_obs, batch_act, batch_logp, batch_ret = [], [], [], []
    episode_rewards = []
    
    for ep in range(n_episodes):
        # 随机选择地图
        mapname = random.choice(maps)
        
        # 运行 episode
        d = run_episode(mapname)
        if d is None:
            continue
        
        # 提取数据
        steps = d.get("steps", 0)
        reward = d.get("total_reward", 0)
        
        # 记录指标
        metrics = {
            "reward": reward,
            "steps": steps,
            "map": mapname,
            "win": reward > 0
        }
        curriculum.record_episode(metrics)
        
        episode_rewards.append(reward)
        
        # 提取轨迹数据
        for step_data in d.get("trajectory", []):
            obs = step_data.get("obs")
            act = step_data.get("act")
            logp = step_data.get("logp")
            ret = step_data.get("ret")
            
            if obs is not None and act is not None:
                batch_obs.append(obs)
                batch_act.append(act)
                if logp is not None:
                    batch_logp.append(logp)
                if ret is not None:
                    batch_ret.append(ret)
    
    return batch_obs, batch_act, batch_logp, batch_ret, episode_rewards

def ppo_update(batch_obs, batch_act, batch_logp, batch_ret):
    """PPO 更新"""
    if len(batch_obs) == 0:
        return 0.0
    
    obs_t = torch.FloatTensor(np.array(batch_obs)).to(DEVICE)
    act_t = torch.LongTensor(batch_act).to(DEVICE)
    old_logp_t = torch.FloatTensor(batch_logp).to(DEVICE)
    ret_t = torch.FloatTensor(batch_ret).to(DEVICE)
    
    total_loss = 0
    for _ in range(EPOCHS):
        dist, values = model(obs_t)
        logp = dist.log_prob(act_t)
        ratio = (logp - old_logp_t).exp()
        surr1 = ratio * ret_t
        surr2 = ratio.clamp(1-CLIP, 1+CLIP) * ret_t
        actor_loss = -torch.min(surr1, surr2).mean()
        critic_loss = (ret_t - values).pow(2).mean()
        entropy = dist.entropy().mean()
        loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy
        
        opt.zero_grad()
        loss.backward()
        opt.step()
        total_loss += loss.item()
    
    return total_loss / EPOCHS

def train_curriculum():
    """课程学习训练主循环"""
    global total_steps
    
    print("="*70)
    print("HoMM3 课程学习训练")
    print("="*70)
    
    # 加载模型
    if os.path.exists(MODEL_PATH):
        try:
            model.load_state_dict(torch.load(MODEL_PATH))
            print(f"Loaded model from {MODEL_PATH}")
        except:
            print(f"Could not load model from {MODEL_PATH}")
    
    # 加载训练状态
    if os.path.exists(STATE_PATH):
        try:
            state = torch.load(STATE_PATH)
            model.load_state_dict(state["model"])
            opt.load_state_dict(state["optimizer"])
            total_steps = state.get("step", 0)
            print(f"Loaded train state from {STATE_PATH}")
        except:
            print(f"Could not load train state from {STATE_PATH}")
    
    total_steps = 0
    
    while True:
        # 获取当前 Level 配置
        level_config = curriculum.get_current_level_config()
        if not level_config:
            print(f"No config for Level {curriculum.current_level}")
            break
        
        maps = curriculum.get_current_maps()
        if not maps:
            print(f"No maps for Level {curriculum.current_level}")
            break
        
        # 获取训练参数
        train_params = curriculum.get_training_params()
        lr = train_params.get("lr", LR)
        clip = train_params.get("clip", CLIP)
        epochs = train_params.get("epochs", EPOCHS)
        batch = train_params.get("batch", BATCH)
        steps_per_ep = train_params.get("steps_per_ep", STEPS_PER_EP)
        
        # 更新优化器学习率
        for param_group in opt.param_groups:
            param_group['lr'] = lr
        
        # 打印状态
        curriculum.print_status()
        
        # 训练一个 batch
        print(f"\nTraining Level {curriculum.current_level}, Episode {curriculum.episode_count+1}-{curriculum.episode_count+batch}")
        print(f"Maps: {len(maps)}")
        
        # 收集轨迹
        batch_obs, batch_act, batch_logp, batch_ret, episode_rewards = collect_trajectories(maps, batch)
        
        if len(batch_obs) > 0:
            # PPO 更新
            loss = ppo_update(batch_obs, batch_act, batch_logp, batch_ret)
            total_steps += len(batch_obs)
            
            # 打印统计
            avg_reward = np.mean(episode_rewards) if episode_rewards else 0
            positive_rate = sum(1 for r in episode_rewards if r > 0) / len(episode_rewards) if episode_rewards else 0
            print(f"  Loss: {loss:.4f}, Avg Reward: {avg_reward:.2f}, Positive Rate: {positive_rate:.2%}")
        
        # 检查晋级
        if curriculum.check_promotion():
            print(f"\n{'='*70}")
            print(f"Level {curriculum.current_level} 晋级条件满足!")
            print(f"{'='*70}")
            
            # 保存当前模型
            save_train_state(STATE_PATH, total_steps)
            torch.save(model.state_dict(), MODEL_PATH)
            
            # 晋级
            if curriculum.promote_to_next_level():
                print(f"晋级到 Level {curriculum.current_level}")
                
                # 检查是否完成所有 Level
                if curriculum.current_level > curriculum.config["curriculum"]["max_level"]:
                    print("\n所有 Level 完成!")
                    break
            else:
                print("晋级失败")
        
        # 检查是否需要延长训练
        elif curriculum.should_extend_training():
            print(f"\n延长 Level {curriculum.current_level} 训练")
        
        # 保存检查点
        if curriculum.episode_count % 100 == 0:
            save_train_state(STATE_PATH, total_steps)
            torch.save(model.state_dict(), MODEL_PATH)
            curriculum._save_state()
    
    # 训练完成
    print("\n" + "="*70)
    print("课程学习训练完成!")
    print("="*70)
    curriculum.print_status()
    
    # 保存最终模型
    save_train_state(STATE_PATH, total_steps)
    torch.save(model.state_dict(), MODEL_PATH)
    curriculum._save_state()

if __name__ == "__main__":
    train_curriculum()
