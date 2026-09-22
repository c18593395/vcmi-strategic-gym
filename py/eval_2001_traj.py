# -*- coding: utf-8 -*-
"""20X20_01 单局 eval + 英雄真实轨迹分析 (对照 20X20_02)
复刻 eval_promo.py 环境参数, 但保留 traj 文件做逐步位置分析"""
import glob, json, os, re, subprocess, sys, time

VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py"
ROOT = "/mnt/d/Bigdata/hero3_fresh"

GUARDS = {
    "T03_adventure_20X20_01.vmap": [(5, 6), (6, 5)],
    "T03_adventure_20X20_02.vmap": [(8, 7), (9, 6)],
}

cks = glob.glob(f"{ROOT}/checkpoints/wsl2_ckpt_*.pt")
ckpt = max(cks, key=lambda f: int(re.search(r"wsl2_ckpt_(\d+)\.pt$", os.path.basename(f)).group(1)))
print(f"ckpt={os.path.basename(ckpt)}")

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
env["CUDA_VISIBLE_DEVICES"] = ""
env["OMP_NUM_THREADS"] = "2"
env["MKL_NUM_THREADS"] = "2"

for mapname in ["T03_adventure_20X20_01.vmap", "T03_adventure_20X20_02.vmap"]:
    traj_out = f"/tmp/eval2001_{mapname.split('_')[-1]}.json"
    cmd = [VENV, RUNNER, "80", traj_out, mapname,
           "--model", ckpt,
           "--blue_ai", "MMAI_RANDOM", "--blue_adventure_ai", "MMAI",
           "--reward_explore", "0.2",
           "--move_to_bias", "1.0", "--move_to_force", "15",
           "--cycle_detect", "5", "--act_loop_penalty", "1.0",
           "--use_nk2_shaping", "--nk2_shaping_scale", "0.3"]
    t0 = time.time()
    print(f"\n=== eval {mapname} ===", flush=True)
    try:
        subprocess.run(cmd, env=env, timeout=300,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tr = json.load(open(traj_out))
    except Exception as e:
        print(f"eval 失败: {e}"); continue
    steps, total_r = tr.get("steps", 0), float(tr.get("total_rew", 0))
    err = tr.get("error", "")
    guards = GUARDS[mapname]
    pos = []
    for nobs in tr.get("nobs", []):
        ah = int(nobs[3203]) if nobs[3203] >= 0 else 0
        b = 128 + ah * 26
        pos.append((int(nobs[b+2]), int(nobs[b+3])))
    print(f"steps={steps} total_r={total_r:.2f} err={err or '-'} ({time.time()-t0:.0f}s)")
    # 前 40 步逐行
    acts = tr.get("act", []); rews = tr.get("rew", [])
    for i in range(min(40, len(pos))):
        hx, hy = pos[i]
        gd = min(abs(hx-gx)+abs(hy-gy) for gx, gy in guards)
        print(f"  {i:3d} a={acts[i]:2d} pos=({hx:2d},{hy:2d}) gd={gd:2d} r={rews[i]:+.2f}")
    visits = sum(1 for p in pos if p in guards)
    mind = min(min(abs(hx-gx)+abs(hy-gy) for gx, gy in guards) for hx, hy in pos)
    uniq = len(set(pos))
    print(f"踏守卫格步数={visits} 最近守卫距离={mind} 去重位置数={uniq}/{len(pos)}")
