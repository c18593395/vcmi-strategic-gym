#!/usr/bin/env python3
"""测试 PPO 模型在真实游戏中表现 — 模型控制动作（带容错）"""
import sys, os, json, time, argparse, traceback

sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

import torch
import torch.nn as nn
import numpy as np
from torch.distributions import Categorical
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(256,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor, self.critic = nn.Linear(128,11), nn.Linear(128,1)
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

ACTIONS = ["→","↘","↓","↙","←","↖","↑","↗","交互","换英雄","结束回合"]

parser = argparse.ArgumentParser()
parser.add_argument("mapname", nargs="?", default="Key to Victory.h3m")
parser.add_argument("--max_turns", type=int, default=20)
parser.add_argument("--model", default="/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt")
parser.add_argument("--blue_ai", default="MMAI_USER")
args = parser.parse_args()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = Net().to(DEVICE)
if os.path.exists(args.model):
    model.load_state_dict(torch.load(args.model, map_location=DEVICE, weights_only=True))
    model.eval()
    print(f"MODEL_LOADED|{args.model}")
else:
    print(f"MODEL_MISSING|{args.model}")
    sys.exit(1)

print(f"GAME_START|{args.mapname}|red=PPO|blue={args.blue_ai}|turns={args.max_turns}", flush=True)

try:
    env = StrategicEnv(
        mapname=args.mapname, max_turns=args.max_turns,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR",
        red="MMAI_USER", blue=args.blue_ai,
        random_heroes=1, boot_timeout=120, vcmi_timeout=60
    )
    
    obs, _ = env.reset()
    print(f"ENV_READY", flush=True)
    
    total_reward = 0
    for turn in range(args.max_turns):
        with torch.no_grad():
            obs_t = torch.tensor(obs, dtype=torch.float32, device=DEVICE).unsqueeze(0)
            pi, val = model(obs_t)
            a = pi.sample().item()
        
        # 打印动作（机器可读格式）
        act_name = ACTIONS[a] if a < len(ACTIONS) else f"({a})"
        
        nobs, r, done, trunc, info = env.step(a)
        total_reward += r
        
        # 关键观测字段
        h1x, h1y = obs[0], obs[1]
        h1_army = sum(obs[5:12]) if len(obs) > 11 else 0
        gold = obs[13] if len(obs) > 13 else 0
        
        print(f"STEP|{turn}|{act_name}|r={r:.1f}|h1=({h1x:.1f},{h1y:.1f})|army={h1_army:.0f}|gold={gold:.0f}|val={val.item():.2f}|done={done or trunc}", flush=True)
        
        obs = nobs
        if done or trunc:
            break
    
    print(f"GAME_END|total_rew={total_reward:.1f}|turns={turn+1}", flush=True)
    env.close()

except Exception as e:
    print(f"ERROR|{type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
