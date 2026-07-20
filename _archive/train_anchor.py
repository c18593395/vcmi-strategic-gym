#!/usr/bin/env python3
"""VCMI-v13 锚点循环训练 — A2 为锚点防止遗忘，逐步引入新图"""
import os, sys, time, subprocess, json
from datetime import datetime

WS = "/home/administrator/vcmi-workspace"
TRAIN_SCRIPT = "/mnt/d/Bigdata/hero3_fresh/train_v13_ppo.py"
VENV = f"{WS}/venv/bin/python"
STEPS_PER_ROUND = 50000

# 策略：eval 胜率反馈驱动 — 弱图(A1/A5/A6)加重，强图(A2)减半
# A1=0% A5=0% A6=0% → 高频；A2=100% → 锚点减半；A3=90% → 保持
SCHEDULE = [
    # Phase 1 (R1-6): 立即救弱图
    "gym/A2.vmap", "gym/A1.vmap", "gym/A5.vmap", "gym/A2.vmap", "gym/A6.vmap", "gym/A1.vmap",
    # Phase 2 (R7-12): 继续弱图 + 试探 A4
    "gym/A5.vmap", "gym/A2.vmap", "gym/A6.vmap", "gym/A4.vmap", "gym/A1.vmap", "gym/A2.vmap",
    # Phase 3 (R13-18): A3 加强 + 新图 A7
    "gym/A5.vmap", "gym/A3.vmap", "gym/A2.vmap", "gym/A6.vmap", "gym/A7.vmap", "gym/A1.vmap",
    # Phase 4 (R19-24): 弱图集中攻克
    "gym/A5.vmap", "gym/A2.vmap", "gym/A1.vmap", "gym/A6.vmap", "gym/A4.vmap", "gym/A2.vmap",
    # Phase 5 (R25-32): 平衡 + A3 回归
    "gym/A5.vmap", "gym/A3.vmap", "gym/A2.vmap", "gym/A1.vmap", "gym/A6.vmap", "gym/A2.vmap",
    "gym/A7.vmap", "gym/A3.vmap",
]
# 权重: A1=5 A2=8 A3=4 A4=2 A5=6 A6=5 A7=2 (A2锚点从53%→25%)

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = f"{WS}/vcmi/rel/bin:{WS}/vcmi_gym/connectors/rel"
env["NO_WANDB"] = "true"
env["VCMI_STEPS"] = str(STEPS_PER_ROUND)
env["VCMI_DEVICE"] = "cuda"  # GPU加速 (RTX3060)

print(f"VCMI-v13 锚点循环训练 | A2=锚点 | {STEPS_PER_ROUND} steps/round")
print(f"共 {len(SCHEDULE)} 轮")
print("=" * 60)

all_results = []
t0 = time.time()
models_dir = f"{WS}/models/v13_ppo"

for round_idx, map_name in enumerate(SCHEDULE):
    t1 = time.time()
    env["VCMI_MAP"] = map_name
    
    print(f"\n{'='*50}")
    print(f"ROUND {round_idx+1}/{len(SCHEDULE)} | MAP: {map_name} | {datetime.now():%H:%M:%S}")
    print(f"{'='*50}")
    
    try:
        ret = subprocess.run(
            [VENV, TRAIN_SCRIPT],
            env=env, cwd=WS, timeout=1200, capture_output=True, text=True
        )
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT (20min) — skipping")
        continue
    
    elapsed = time.time() - t1
    print(f"DONE | {elapsed/60:.1f}min | exit={ret.returncode}")
    
    # Extract key metrics: train_v13_ppo.py _on_rollout_end format:
    #   [{step}] rew={rew} win={win} loss={loss} clip={clip} ev={ev} fps={fps}
    # Multiple rollout lines per round; last line has final values.
    win_rate = None
    ev = None
    for line in ret.stdout.split('\n') + ret.stderr.split('\n'):
        if 'win=' in line:
            try:
                tokens = line.strip().split()
                for tok in tokens:
                    if tok.startswith('win='):
                        win_rate = float(tok.split('=')[1])
            except: pass
        if 'ev=' in line:
            try:
                tokens = line.strip().split()
                for tok in tokens:
                    if tok.startswith('ev='):
                        ev = float(tok.split('=')[1])
            except: pass
    
    wr_str = f"win={win_rate:.0%}" if win_rate is not None else "win=?"
    ev_str = f"ev={ev:.3f}" if ev is not None else "ev=?"
    print(f"  {wr_str} {ev_str}")
    
    result = {
        "round": round_idx + 1,
        "map": map_name,
        "elapsed": elapsed,
        "exit": ret.returncode,
        "win_rate": win_rate,
        "explained_variance": ev,
    }
    all_results.append(result)
    
    # Show last few lines
    for line in ret.stdout.strip().split('\n')[-5:]:
        if line.strip() and not line.startswith('|'):
            print(f"  {line.strip()[:100]}")
    
    time.sleep(2)  # brief pause between rounds

total = time.time() - t0
print(f"\n{'='*60}")
print(f"全部完成 ({total/60:.1f}min / {len(SCHEDULE)}轮)")
