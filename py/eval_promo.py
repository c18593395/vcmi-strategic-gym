#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2: 晋级判据自动化 eval — 拿 checkpoint 打固定基线局 (CPU-only, 独立实例, 不碰训练)

设计 (任务清单 P2 / B4 规格):
  - 逐局子进程调用 ep_runner_one.py (训练同款参数 → 奖励/胜负口径与训练完全一致)
  - CPU-only: CUDA_VISIBLE_DEVICES="" + OMP/MKL 线程=2, 不抢训练 GPU
  - 每局超时 kill, 崩溃局计 0 分不中断
  - 判定与 analyze_ab.py 同口径: 首胜 = r>=80 且 steps<60; 晋级线 = 胜率>=30% 或 avg_r>0
  - 结果追加 py/eval_history.jsonl 供趋势跟踪; 晋级重启步保留人工确认 (本脚本只提示不执行)

用法 (训练运行期间可安全执行, 频率 >=2h 一次):
  wsl bash -c "cd /mnt/d/Bigdata/hero3_fresh && /home/administrator/vcmi-workspace/venv/bin/python py/eval_promo.py --episodes 6"
  可选: --ckpt <路径> (默认取 checkpoints/ 最新 wsl2_ckpt_*.pt), --maps 逗号分隔地图名
"""
import argparse, glob, json, os, re, subprocess, sys, time

ROOT = "/mnt/d/Bigdata/hero3_fresh"
VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = f"{ROOT}/ep_runner_one.py"
HIST = f"{ROOT}/py/eval_history.jsonl"
WIN_R, WIN_STEPS = 80.0, 60          # 首胜判定 (与 analyze_ab.py 一致)
PROMO_WIN_RATE = 0.30                # 晋级线①
PROMO_AVG_R = 0.0                    # 晋级线②
DEFAULT_MAPS = "T03_adventure_20X20_01.vmap,T03_adventure_20X20_02.vmap"

ap = argparse.ArgumentParser()
ap.add_argument("--episodes", type=int, default=6, help="总局数 (地图轮换)")
ap.add_argument("--ckpt", type=str, default=None, help="checkpoint 路径 (默认最新 wsl2_ckpt_*.pt)")
ap.add_argument("--maps", type=str, default=DEFAULT_MAPS, help="逗号分隔地图名 (裸文件名)")
ap.add_argument("--timeout", type=int, default=900, help="单局超时秒")
ap.add_argument("--steps", type=int, default=200, help="单局步数上限 (训练同款)")
args = ap.parse_args()

# --- checkpoint ---
ckpt = args.ckpt
if not ckpt:
    cks = glob.glob(f"{ROOT}/checkpoints/wsl2_ckpt_*.pt")
    if not cks:
        print("ERROR: checkpoints/ 下无 wsl2_ckpt_*.pt, 用 --ckpt 指定"); sys.exit(1)
    ckpt = max(cks, key=lambda f: int(re.search(r"wsl2_ckpt_(\d+)\.pt$", os.path.basename(f)).group(1)))
step_m = re.search(r"wsl2_ckpt_(\d+)\.pt$", os.path.basename(ckpt))
ckpt_step = int(step_m.group(1)) if step_m else -1
print(f"[eval] ckpt={ckpt} (step={ckpt_step})")

maps = [m.strip() for m in args.maps.split(",") if m.strip()]
env = os.environ.copy()
env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
env["CUDA_VISIBLE_DEVICES"] = ""     # CPU-only
env["OMP_NUM_THREADS"] = "2"
env["MKL_NUM_THREADS"] = "2"

results = []
for i in range(args.episodes):
    mapname = maps[i % len(maps)]
    traj_out = f"/tmp/eval_traj_{os.getpid()}_{i}.json"
    cmd = [VENV, RUNNER, str(args.steps), traj_out, mapname,
           "--model", ckpt,
           "--blue_ai", "MMAI_RANDOM", "--blue_adventure_ai", "MMAI",   # 训练同款对手
           "--reward_explore", "0.2",
           "--move_to_bias", "1.0", "--move_to_force", ("60" if mapname.startswith("T04") else "15"),
           # T04 强制期 60 与训练同口径 (2026-08-29); T03 维持 15 (历史 eval 口径)
           "--cycle_detect", "5", "--act_loop_penalty", "1.0",
           "--guard_done_steps", "15",                                   # 训练同款: 守卫击杀自动终局 (2026-08-29)
           "--objective_reward", "30",                                   # 训练同款: T04 首占矿/首进城镇 +30 (2026-08-29)
           "--use_nk2_shaping", "--nk2_shaping_scale", "0.3"]
    t0 = time.time()
    try:
        subprocess.run(cmd, env=env, timeout=args.timeout,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(traj_out) as f:
            tr = json.load(f)
        steps, total_r = tr.get("steps", 0), float(tr.get("total_rew", 0.0))
        err = tr.get("error", "")
    except subprocess.TimeoutExpired:
        steps, total_r, err = 0, 0.0, "timeout"
    except Exception as e:
        steps, total_r, err = 0, 0.0, str(e)
    finally:
        if os.path.exists(traj_out): os.remove(traj_out)
    win = 1 if (total_r >= WIN_R and 0 < steps < WIN_STEPS) else 0
    results.append({"map": mapname, "steps": steps, "r": round(total_r, 2), "win": win, "err": err})
    print(f"[eval] ep{i+1}/{args.episodes} map={mapname} steps={steps} r={total_r:.2f} win={win} err={err or '-'} ({time.time()-t0:.0f}s)")

# --- 汇总 ---
n = len(results)
wins = sum(r["win"] for r in results)
avg_r = sum(r["r"] for r in results) / n
errs = sum(1 for r in results if r["err"])
win_rate = wins / n
verdict = []
if win_rate >= PROMO_WIN_RATE: verdict.append(f"线①胜率{win_rate:.0%}>=30% ✅")
else: verdict.append(f"线①胜率{win_rate:.0%}<30% ⬜")
if avg_r > PROMO_AVG_R: verdict.append(f"线②avg_r={avg_r:.1f}>0 ✅")
else: verdict.append(f"线②avg_r={avg_r:.1f}<=0 ⬜")
hit = (win_rate >= PROMO_WIN_RATE or avg_r > PROMO_AVG_R)
if n < 10:
    promo = "样本不足 (n<10, 增加局数后再判)" if hit else "未达标"
else:
    promo = "达标提示 (晋级需人工确认重启)" if hit else "未达标"
print(f"\n[eval] SUMMARY n={n} win_rate={win_rate:.1%} avg_r={avg_r:.2f} errors={errs}")
print(f"[eval] 晋级线: {' | '.join(verdict)}  →  {promo}")

# --- 历史趋势 ---
rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "ckpt_step": ckpt_step, "n": n,
       "win_rate": round(win_rate, 3), "avg_r": round(avg_r, 2), "errors": errs, "results": results}
with open(HIST, "a") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
if os.path.exists(HIST):
    lines = open(HIST).read().strip().split("\n")
    if len(lines) >= 2:
        prev = json.loads(lines[-2])
        print(f"[eval] 趋势 vs 上次({prev['ts']}, ckpt={prev['ckpt_step']}): "
              f"win_rate {prev['win_rate']:.0%}→{win_rate:.0%}, avg_r {prev['avg_r']}→{avg_r:.2f}")
print(f"[eval] 历史已写入 {HIST}")
