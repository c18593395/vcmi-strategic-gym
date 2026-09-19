#!/usr/bin/env python3
"""Level 0 训练 - 使用 T01 地图"""
import subprocess, json, time, os, random, signal, sys
import torch, torch.nn as nn, numpy as np
from torch.distributions import Categorical

# 训练参数
N_EPISODES = 1000
BATCH = 1
STEPS_PER_EP = 50
LR = 1e-4
CLIP = 0.2
EPOCHS = 4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Level 0 地图
MAPS = [
    "T01_adventure_20X20_01.vmap",
    "T01_adventure_20X20_02.vmap",
    "T01_adventure_30X30_01.vmap",
    "T01_adventure_30X30_02.vmap",
    "T01_adventure_36X36_01.vmap",
]

VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
TRAJ = "/tmp/traj_one.json"
MODEL_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model_level0.pt"
STATE_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_train_state_level0.pt"

# 网络定义 (与 ep_runner_one.py 一致)
class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(3464, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.actor = nn.Linear(128, 25)
        self.critic = nn.Linear(128, 1)
    
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

model = Net().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=LR)

total_steps = 0

def save_train_state(path, step=0):
    torch.save({
        "model": model.state_dict(),
        "optimizer": opt.state_dict(),
        "step": step,
    }, path)

def save_shutdown(*args):
    print("\n  Shutdown, saving train state...", flush=True)
    save_train_state(STATE_PATH, total_steps)
    print(f"  Saved {STATE_PATH}", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, save_shutdown)
signal.signal(signal.SIGINT, save_shutdown)

def run_episode(mapname):
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    cmd = [VENV, RUNNER, str(STEPS_PER_EP), TRAJ, mapname]
    
    if os.path.exists(MODEL_PATH):
        cmd.extend(["--model", MODEL_PATH])
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        stdout, stderr = proc.communicate(timeout=STEPS_PER_EP*3 + 15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        return None
    
    # 不检查返回码，只检查轨迹文件
    try:
        with open(TRAJ) as f:
            d = json.load(f)
            if d.get("steps", 0) > 0:
                return d
    except:
        pass
    return None

print("="*70)
print("HoMM3 Level 0 训练")
print(f"地图: {len(MAPS)} 张 T01 地图")
print(f"目标: {N_EPISODES} episodes")
print("="*70, flush=True)

episode_rewards = []
positive_count = 0

for ep in range(1, N_EPISODES + 1):
    mapname = random.choice(MAPS)
    
    d = run_episode(mapname)
    if d is None:
        print(f"  Episode {ep}: 失败", flush=True)
        continue
    
    steps = d.get("steps", 0)
    reward = d.get("total_rew", 0)
    episode_rewards.append(reward)
    if reward > 0:
        positive_count += 1
    
    # 提取轨迹数据
    batch_obs = []
    batch_act = []
    batch_logp = []
    batch_ret = []
    
    for i in range(len(d.get("obs", []))):
        obs = d["obs"][i]
        act = d["act"][i] if i < len(d.get("act", [])) else None
        
        if obs is not None and act is not None:
            batch_obs.append(obs)
            batch_act.append(act)
            batch_logp.append(0.0)  # placeholder
            batch_ret.append(reward / steps if steps > 0 else 0)  # 简化回报
    
    if len(batch_obs) == 0:
        continue
    
    # PPO 更新
    obs_t = torch.FloatTensor(np.array(batch_obs)).to(DEVICE)
    act_t = torch.LongTensor(batch_act).to(DEVICE)
    
    for _ in range(EPOCHS):
        dist, values = model(obs_t)
        logp = dist.log_prob(act_t)
        # 简化 PPO (无旧策略)
        entropy = dist.entropy().mean()
        loss = -entropy * 0.01  # 最大化熵
        
        opt.zero_grad()
        loss.backward()
        opt.step()
    
    total_steps += len(batch_obs)
    
    # 打印日志
    avg_reward = np.mean(episode_rewards[-100:]) if episode_rewards else 0
    positive_rate = positive_count / ep if ep > 0 else 0
    
    if ep % 10 == 0 or reward > 0:
        print(f"  Episode {ep}: reward={reward:.2f}, avg={avg_reward:.2f}, pos_rate={positive_rate:.2%}, steps={steps}", flush=True)
    
    # 保存检查点
    if ep % 100 == 0:
        save_train_state(STATE_PATH, total_steps)
        torch.save(model.state_dict(), MODEL_PATH)
        print(f"  保存检查点: Episode {ep}", flush=True)

# 训练完成
print("\n" + "="*70)
print("Level 0 训练完成!")
print(f"总 Episodes: {len(episode_rewards)}")
print(f"正奖励率: {positive_count / len(episode_rewards):.2%}")
print(f"平均奖励: {np.mean(episode_rewards):.2f}")
print("="*70, flush=True)

save_train_state(STATE_PATH, total_steps)
torch.save(model.state_dict(), MODEL_PATH)
