# -*- coding: utf-8 -*-
"""0829 冒烟: 验证 08-27 版本对 (libmlclient=77967cde + libMMAI=13c0f041) 战斗不再触发 QueryID 断言.
参数与 train_wsl2_ppo_v2.py 完全同款: red=StupidAI+checkpoint, blue=MMAI_RANDOM, blue_adventure_ai=MMAI.
运行: wsl bash -c "cd /mnt/d/Bigdata/hero3_fresh && venv/bin/python py/smoke_pair_0829.py 2>&1 | tee /tmp/smoke_pair_0829.log"
判定: 无 'QueryID is -1' 且 steps>1 → PASS
"""
import os, sys, glob, time
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

# 训练同款 checkpoint (ep_runner 子进程用临时 ckpt, 这里取最新正式 ckpt)
import re as _re
ckpts = sorted(glob.glob("/mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_ckpt_*.pt"),
               key=lambda f: int(_re.search(r"wsl2_ckpt_(\d+)\.pt$", os.path.basename(f)).group(1)))
model = ckpts[-1] if ckpts else "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt"
print(f"[smoke] model={model}")

mapname = "T03_adventure_20X20_01.vmap"  # 训练同款: 裸文件名, 引擎从 data/Maps 解析
env = StrategicEnv(
    mapname=mapname, max_turns=20,
    vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    vcmienv_loglevel="ERROR", red="StupidAI", blue="MMAI_RANDOM",
    random_heroes=0, boot_timeout=120, vcmi_timeout=900,
    red_model_path=model,
    blue_adventure_ai="MMAI",
)
obs, info = env.reset()
print(f"[smoke] reset OK obs_nz={(obs>0).sum()}")
steps, total_r, done = 0, 0.0, False
t0 = time.time()
act_seq = []
while not done and steps < 60:
    # 训练同款: 前 30 步强制 MOVE_TO(24) (move_to_force), 走向守卫触发战斗; 之后轮询 8 方向
    a = 24 if steps < 30 else steps % 8
    nobs, r, term, trunc, info = env.step(a)
    total_r += r
    steps += 1
    done = term or trunc
    act_seq.append(a)
    if steps % 5 == 0 or done:
        print(f"[smoke] step={steps} act={act_seq[-5:]} r={r:.2f} tot={total_r:.2f} done={done} t={time.time()-t0:.0f}s")
env.close()
print(f"[smoke] RESULT steps={steps} total_r={total_r:.2f} -> {'PASS' if steps > 1 else 'FAIL(step=1)'}")
