#!/usr/bin/env python3
"""VCMI-v13 循环训练 - 流式输出"""
import os, sys, time, subprocess, glob
from datetime import datetime

WS = "/home/administrator/vcmi-workspace"
MODEL_DIR = f"{WS}/models/v13_ppo"

print("=" * 50)
print(f"VCMI-v13 循环训练 | {datetime.now():%H:%M:%S}")
print("=" * 50)

r = 0
while True:
    r += 1
    print(f"\n{'='*40}")
    print(f"ROUND {r} START | {datetime.now():%H:%M:%S}")
    print(f"{'='*40}")
    t0 = time.time()
    
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = f"{WS}/vcmi/rel/bin:{WS}/vcmi_gym/connectors/rel"
    
    # 流式输出，不捕获
    ret = subprocess.run(
        [f"{WS}/venv/bin/python", "/mnt/d/Bigdata/hero3_fresh/train_v13_ppo.py"],
        env=env, cwd=WS, timeout=3600
    )
    
    elapsed = time.time() - t0
    m = f"{elapsed:.0f}s" if elapsed<60 else f"{elapsed/60:.1f}min"
    print(f"\nROUND {r} DONE | {m} | {datetime.now():%H:%M:%S}")
    
    # 清理旧 checkpoint
    files = sorted(glob.glob(f"{MODEL_DIR}/v13_ppo_*_steps.zip"))
    for f in files[:-2]:
        os.remove(f)
