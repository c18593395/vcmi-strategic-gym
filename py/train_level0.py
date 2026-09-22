#!/usr/bin/env python3
"""
Level 0 专用训练脚本
使用 T01 地图 (无障碍基础地图) 训练
"""

import subprocess, json, time, os, random, signal, sys
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

# === 训练参数 ===
N_EPISODES = 1000
BATCH = 128
STEPS_PER_EP = 50
LR = 1e-4
CLIP = 0.2
EPOCHS = 4
GAMMA = 0.99
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === Level 0 地图 (T01 系列) ===
MAPS = [
    "T01_adventure_20X20_01.vmap",
    "T01_adventure_20X20_02.vmap",
    "T01_adventure_30X30_01.vmap",
    "T01_adventure_30X30_02.vmap",
    "T01_adventure_36X36_01.vmap",
]

# === 路径配置 ===
VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py"
TRAJ = "/tmp/traj_one.json"
MODEL_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model_level0.pt"
STATE_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_train_state_level0.pt"
LOG_PATH = "/mnt/d/Bigdata/hero3_fresh/train_level0.log"

# === 网络定义 (必须与 ep_runner_one.py 一致) ===
class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(3464, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.actor = nn.Linear(128, 25)
        self.critic = nn.Linear(128, 1)
    
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

# === 初始化 ===
model = Net().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=LR)

# 日志文件
log_file = open(LOG_PATH, 'a')

def log(msg):
    """写入日志"""
    print(msg, flush=True)
    log_file.write(msg + '\n')
    log_file.flush()

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
    try:
        print("\n  Shutdown, saving train state...", flush=True)
        save_train_state(STATE_PATH, total_steps)
        print(f"  Saved {STATE_PATH}", flush=True)
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGTERM, save_shutdown)
signal.signal(signal.SIGINT, save_shutdown)

def run_episode(mapname):
    """运行一个 episode"""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    cmd = [VENV, RUNNER, str(STEPS_PER_EP), TRAJ, mapname]
    
    # 如果有模型，使用模型
    if os.path.exists(MODEL_PATH):
        cmd.extend(["--model", MODEL_PATH])
    
    log(f"  Running: map={mapname}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        stdout, stderr = proc.communicate(timeout=STEPS_PER_EP*3 + 15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        log(f"  Timeout!")
        return None
    
    # 检查返回码 (忽略警告)
    if proc.returncode != 0:
        stderr_str = stderr.decode() if stderr else ""
        # 只打印前200字符
        log(f"  Warning: returncode={proc.returncode}")
        # 不返回 None，继续尝试读取轨迹
    
    try:
        with open(TRAJ) as f:
            d = json.load(f)
            if d.get("steps", 0) > 0 and not d.get("error"):
                return d
            else:
                log(f"  Invalid trajectory: steps={d.get('steps', 0)}, error={d.get('error', 'none')}")
    except Exception as e:
        log(f"  Parse error: {e}")
    return None

def train_level0():
    """Level 0 训练主循环"""
    global total_steps
    
    log("="*70)
    log("HoMM3 Level 0 训练")
    log(f"地图: {len(MAPS)} 张 T01 地图")
    log(f"目标: {N_EPISODES} episodes")
    log("="*70)
    
    total_steps = 0
    episode_rewards = []
    positive_count = 0
    
    for ep in range(1, N_EPISODES + 1):
        # 随机选择地图
        mapname = random.choice(MAPS)
        
        # 运行 episode
        d = run_episode(mapname)
        if d is None:
            log(f"  Episode {ep}: 失败")
            continue
        
        # 提取数据
        steps = d.get("steps", 0)
        reward = d.get("total_reward", 0)
        
        # 记录指标
        episode_rewards.append(reward)
        if reward > 0:
            positive_count += 1
        
        # 提取轨迹数据
        batch_obs = []
        batch_act = []
        batch_logp = []
        batch_ret = []
        
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
        
        if len(batch_obs) == 0:
            continue
        
        # PPO 更新
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
        
        total_steps += len(batch_obs)
        avg_loss = total_loss / EPOCHS
        
        # 计算统计
        avg_reward = np.mean(episode_rewards[-100:]) if episode_rewards else 0
        positive_rate = positive_count / ep if ep > 0 else 0
        
        # 打印日志
        if ep % 10 == 0 or reward > 0:
            log(f"  Episode {ep}: reward={reward:.2f}, avg_reward={avg_reward:.2f}, positive_rate={positive_rate:.2%}, steps={steps}")
        
        # 保存检查点
        if ep % 100 == 0:
            save_train_state(STATE_PATH, total_steps)
            torch.save(model.state_dict(), MODEL_PATH)
            log(f"  保存检查点: Episode {ep}")
    
    # 训练完成
    log("\n" + "="*70)
    log("Level 0 训练完成!")
    log(f"总 Episodes: {len(episode_rewards)}")
    log(f"正奖励率: {positive_count / len(episode_rewards):.2%}")
    log(f"平均奖励: {np.mean(episode_rewards):.2f}")
    log("="*70)
    
    # 保存最终模型
    save_train_state(STATE_PATH, total_steps)
    torch.save(model.state_dict(), MODEL_PATH)
    log(f"模型已保存: {MODEL_PATH}")

if __name__ == "__main__":
    train_level0()
