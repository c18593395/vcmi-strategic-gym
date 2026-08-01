#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C8.5 复现: ep_runner_one 同参数, DEBUG 日志抓终止原因"""
import sys, os, time
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
import torch, torch.nn as nn
from torch.distributions import Categorical
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(264,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor, self.critic = nn.Linear(128,11), nn.Linear(128,1)
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

model = Net()
sd = torch.load("/mnt/d/Bigdata/hero3_fresh/bc_model.pt", map_location="cpu", weights_only=True)
model.load_state_dict(sd)
model.eval()

env = StrategicEnv(
    mapname="Dungeon Keeper.h3m", max_turns=200,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="debug",
    vcmienv_loglevel="DEBUG", red="StupidAI", blue="MMAI_RANDOM",
 random_heroes=1, boot_timeout=120, vcmi_timeout=120,
 red_model_path="/mnt/d/Bigdata/hero3_fresh/bc_model.pt",
 blue_adventure_ai="MMAI",
    reward_explore=1.0,
)
t0 = time.time()
obs, info = env.reset()
print(f"[repro] reset {time.time()-t0:.0f}s day={info.get('day')} obs_nz={(obs>0).sum()}", flush=True)
for i in range(10):
    with torch.no_grad():
        obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
        pi, _ = model(obs_t)
        passable = torch.tensor(obs[-8:], dtype=torch.bool)
        logits = pi.logits[0].clone()
        if passable.any():
            logits[:8][~passable] = float('-inf')
            a = Categorical(logits=logits).sample().item()
        else:
            a = 10
    t1 = time.time()
    a = 0  # 强制移动测试
    try:
        nobs, r, term, trunc, info2 = env.step(a)
        print(f"[repro] step{i} act={a} {time.time()-t1:.0f}s r={r} term={term} trunc={trunc} day={info2.get('day')} go={info2.get('game_over')}", flush=True)
    except Exception as e:
        print(f"[repro] step{i} act={a} EXC {time.time()-t1:.0f}s: {e}", flush=True)
        # 尝试 END_TURN 解卡
        t2 = time.time()
        try:
            env._send_action(10)
            env._adventure_wait(timeout=30)
            print(f"[repro] END_TURN 解卡成功 {time.time()-t2:.0f}s", flush=True)
        except Exception as e2:
            print(f"[repro] END_TURN 解卡失败: {e2}", flush=True)
        break
    if term or trunc:
        print(f"[repro] TERMINATED at step{i}, 尝试 END_TURN 解卡", flush=True)
        env._terminated = False
        env._truncated = False
        t2 = time.time()
        try:
            env._send_action(10)
            env._adventure_wait(timeout=60)
            print(f"[repro] END_TURN 解卡成功 {time.time()-t2:.0f}s", flush=True)
            st = env._read_state()
            print(f"[repro] 解卡后 day={st.day if st else None}", flush=True)
        except Exception as e2:
            print(f"[repro] END_TURN 解卡失败: {e2}", flush=True)
        break
    obs = nobs
env.close()
print("[repro] done", flush=True)
