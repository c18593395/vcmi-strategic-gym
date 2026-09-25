#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C1/P2: 晋级判据自动化 eval — 冻结 checkpoint 打固定基线局 (CPU-only, 独立实例, 不碰训练)

与 py/check_win1_watch.py 的分工:
  - check_win1_watch = 在线观测生产训练流 (含探索强制/对手池漂移), 判 WIN-1 观察窗
  - eval_promo (本脚本) = 冻结 ckpt × 固定基线参数离线评估, 供晋级横向比较与趋势跟踪

09-14 重写 (C1 收口, P2 初版 08-29 已过时):
  - 基线池 T03 20X20 → 当前 MAPS=10 (train_wsl2_ppo_v2.py L48-78), profile 可选
  - 奖励参数对齐生产 (train_wsl2_ppo_v2.py L148-187): explore 0.3 / nk2 0.45 /
    economy_force 24 / move_to_bias 1.0 (稳态 move_scale=0.5×2.0) / move_to_force 60(T05/T06) /
    cycle_detect 5 / act_loop_penalty 1.0 / guard_done_steps 15 / objective_reward 30 /
    death_penalty -50 (ep_runner 默认, 显式传防漂移)
  - 大图判据取代小图首胜 (r>=80/steps<60 在 72/108 图恒假/恒真无区分度):
    1v3 组用课程面板 (capture 率/守卫闭环/自发经济/200 截断/avg_r), 与 WIN-1 同口径
  - 09-14 三道拦截口径: 子进程 rc!=0 / traj mapname 身份不符 → invalid 不计分
  - 低频护栏: 距上次 eval < --min-interval (默认 7200s) 拒绝执行 (--force 绕过)
  - 串行 + OMP/MKL=2 线程, 不抢训练 GPU/CPU; 结果追加 py/eval_history.jsonl

用法 (训练运行期间可安全执行, 频率 >=2h 一次):
  wsl bash -c "cd /mnt/d/Bigdata/hero3_fresh && /home/administrator/vcmi-workspace/venv/bin/python py/eval_promo.py"
  可选:
    --profile all|1v3|duel|t05|king|legacy  (默认 all = MAPS=10 每图 1 局共 10 局)
    --episodes N      覆盖局数 (按 profile 地图轮换; 默认 = profile 地图数)
    --ckpt <路径>     默认 checkpoints/ 最新 wsl2_ckpt_*.pt
    --timeout 2400    单局超时秒 (大图慢局 9s/步×200≈1800s, 默认留足)
    --min-interval 7200 / --force

实测注意 (09-14 冒烟):
  - CUDA_VISIBLE_DEVICES 只限 GPU, vcmiserver 引擎线程仍吃 CPU → 与训练并发时双方都变慢,
    36X36 单局从 ~80s 拉长到 >600s。大图 all(10 局) 建议在训练低峰跑, 或先用 t05/1v3 小批量。
  - 每局在独立进程组启动, 父进程收 SIGTERM/SIGINT 会连带 kill 整个局 (不留 vcmiserver 孤儿)。
  - 外层调度 timeout 必须 > --timeout, 给 Python 侧看门狗留出杀局+汇总时间。
"""
import os
import argparse, glob, json, os, re, signal, subprocess, sys, threading, time

ROOT = os.environ.get("ROOT", "/mnt/d/Bigdata/hero3_fresh")
VENV = os.environ.get("VENV", "/home/administrator/vcmi-workspace/venv/bin/python")
RUNNER = f"{ROOT}/py/ep_runner_one.py"
HIST = f"{ROOT}/py/eval_history.jsonl"

# --- 基线地图池 (与 train_wsl2_ppo_v2.py MAPS 一致, 09-14) ---
MAP_T05 = [
    "T05_adventure_36X36_01.vmap",
    "T05_adventure_52X52_01.vmap",
    "T05_adventure_52X52_02.vmap",
]
MAP_T06_DUEL = [
    "T06_adventure_72X72_01_duel.vmap",
    "T06_adventure_72X72_02_duel.vmap",
    "T06_adventure_108X108_02_duel.vmap",
]
MAP_T06_1V3 = [
    "T06_adventure_72X72_01.vmap",
    "T06_adventure_72X72_02.vmap",
    "T06_adventure_108X108_02.vmap",
]
MAP_KING = ["King_of_Pain_h3m.vmap"]
MAP_LEGACY = [  # P2 历史口径, T03 已毕业, 仅保留可复现比较
    "T03_adventure_20X20_01.vmap",
    "T03_adventure_20X20_02.vmap",
]
PROFILES = {
    "all": MAP_T05 + MAP_T06_DUEL + MAP_T06_1V3 + MAP_KING,   # 10
    "1v3": MAP_T06_1V3,
    "duel": MAP_T06_DUEL,
    "t05": MAP_T05,
    "king": MAP_KING,
    "legacy": MAP_LEGACY,
}

# 小图首胜口径 (legacy profile; 与 analyze_ab.py / P2 一致)
WIN_R, WIN_STEPS = 80.0, 60
PROMO_WIN_RATE = 0.30

# --- B4 晋级判据常量 (方案_B1-B4 L83-105, 双条件口径) ---
B4_GUARD_PRIME_RATE = 0.30   # ① GUARD 首胜率 (guard>0 占比) ≥30%
B4_POS_RATE_MIN = 0.70       # ② 正局率 (r>0 占比) ≥70%
B4_AVG_R_MIN = 15.0          # ③ avg_r ≥+15
B4_AVG_R_WINDOWS = 3        # ③ 连续 3 个 100 局窗口
B4_BIG_NEG_MAX = 0.0        # ④ 大负率 (r<-100 占比) 保持 0
B4_BIG_NEG_TH = -100.0      # 大负阈值

ap = argparse.ArgumentParser()
ap.add_argument("--profile", choices=list(PROFILES), default="all")
ap.add_argument("--episodes", type=int, default=None, help="默认 = profile 地图数")
ap.add_argument("--ckpt", type=str, default=None)
ap.add_argument("--timeout", type=int, default=2400)
ap.add_argument("--steps", type=int, default=200)
ap.add_argument("--min-interval", type=int, default=7200, help="距上次 eval 最小秒数 (默认 2h)")
ap.add_argument("--force", action="store_true", help="绕过低频护栏")
args = ap.parse_args()

# --- 低频护栏 (C1: 训练期间 eval 频率 >=2h, 防抢 CPU) ---
if not args.force and os.path.exists(HIST):
    try:
        last_line = open(HIST).read().strip().split("\n")[-1]
        last_ts = json.loads(last_line).get("ts")
        if last_ts:
            dt = time.time() - time.mktime(time.strptime(last_ts, "%Y-%m-%d %H:%M:%S"))
            if dt < args.min_interval:
                wait = int(args.min_interval - dt)
                print(f"[eval] 距上次 eval 仅 {int(dt)}s (<{args.min_interval}s), "
                      f"请 {wait}s 后再跑, 或加 --force 绕过 (C1 低频护栏)")
                sys.exit(2)
    except Exception:
        pass  # history 损坏不阻断评估

# --- checkpoint ---
ckpt = args.ckpt
if not ckpt:
    cks = glob.glob(f"{ROOT}/checkpoints/wsl2_ckpt_*.pt")
    if not cks:
        print("ERROR: checkpoints/ 下无 wsl2_ckpt_*.pt, 用 --ckpt 指定"); sys.exit(1)
    ckpt = max(cks, key=lambda f: int(re.search(r"wsl2_ckpt_(\d+)\.pt$", os.path.basename(f)).group(1)))
m = re.search(r"wsl2_ckpt_(\d+)\.pt$", os.path.basename(ckpt))
ckpt_step = int(m.group(1)) if m else -1
print(f"[eval] profile={args.profile} ckpt={ckpt} (step={ckpt_step})")

maps = PROFILES[args.profile]
n_ep = args.episodes or len(maps)
env = os.environ.copy()
env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
env["CUDA_VISIBLE_DEVICES"] = ""     # CPU-only, 不抢训练 GPU
env["OMP_NUM_THREADS"] = "2"
env["MKL_NUM_THREADS"] = "2"

def group_of(mp):
    if "duel" in mp:
        return "duel"
    if mp.startswith("T06"):
        return "1v3"
    if mp.startswith("T05"):
        return "T05"
    return "H3M"

def parse_events(out):
    """从 ep_runner stdout 解析白名单事件 (口径同 train 主日志转储)。"""
    ev = {"capture": 0, "guard": 0, "guard_done": 0, "zombie": 0, "hero_death": 0,
          "mine": 0, "recruited": 0, "build_new": 0}
    for line in out.splitlines():
        if "[TOWN_CAPTURE]" in line: ev["capture"] += 1
        elif "[GUARD_DONE]" in line: ev["guard_done"] += 1
        elif "[GUARD]" in line: ev["guard"] += 1          # 必须在 GUARD_DONE 之后判
        elif "[HERO_DEATH]" in line: ev["hero_death"] += 1
        elif "[ZOMBIE]" in line: ev["zombie"] += 1
        elif "[MINE]" in line: ev["mine"] += 1
        elif "[RECRUITED]" in line: ev["recruited"] += 1
        elif "[BUILD_NEW]" in line: ev["build_new"] += 1
    return ev

def spont(acts):
    """自发经济: 强制窗(前24拍)外的 16-21, 同 check_duel_watch / check_win1_watch 口径。"""
    return sum(1 for i, a in enumerate(acts) if i >= 24 and 16 <= a <= 21)

results = []
_cur_proc = {"p": None}

def _kill_cur():
    p = _cur_proc.get("p")
    if p is not None and p.poll() is None:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

def _on_signal(signum, _frame):
    print(f"\n[eval] 收到信号 {signum}, 终止当前局子进程组后退出", flush=True)
    _kill_cur()
    sys.exit(128 + signum)

signal.signal(signal.SIGTERM, _on_signal)
signal.signal(signal.SIGINT, _on_signal)

# 训练并发软提醒 (不阻断; OMP=2 只限 BLAS, vcmiserver 仍吃 CPU)
try:
    n_srv = len(subprocess.run(["pgrep", "-f", "vcmiserver"], capture_output=True).stdout.split())
    if n_srv > 0:
        print(f"[eval] ⚠ 检测到 {n_srv} 个 vcmiserver 在跑 (训练中): CPU 并发会拖慢双方, "
              f"大 profile 建议错峰; Ctrl-C 可随时安全中止 (本局子进程组连带清理)", flush=True)
except Exception:
    pass

LIVE_TAGS = ("[TOWN_CAPTURE]", "[GUARD]", "[MINE]", "[HERO_DEATH]", "[ZOMBIE]",
             "[EP_TIME]", "[ERROR]", "Assertion", "[GUARD_DONE]")

for i in range(n_ep):
    mapname = maps[i % len(maps)]
    traj_out = f"/tmp/eval_traj_{os.getpid()}_{i}.json"
    if os.path.exists(traj_out):
        os.remove(traj_out)
    # 生产稳态参数: ep_runner L134-136 对 T06 无条件覆盖 force=200/guard_done=0
    # (此处传 60/15 对 T06 无效但与生产被覆盖后的结果一致; T04/T05 用传入值 15/15)
    force = 60 if mapname.startswith(("T04", "T05", "T06")) else 15
    cmd = [VENV, RUNNER, str(args.steps), traj_out, mapname,
           "--model", ckpt,
           "--blue_ai", "MMAI_RANDOM", "--blue_adventure_ai", "MMAI",
           "--reward_explore", "0.3",
           "--move_to_bias", "1.0", "--move_to_force", str(force),
           "--economy_force", "24",
           "--cycle_detect", "5", "--act_loop_penalty", "1.0",
           "--guard_done_steps", "15", "--objective_reward", "30",
           "--death_penalty", "-50",
           "--use_nk2_shaping", "--nk2_shaping_scale", "0.45"]
    t0 = time.time()
    out_lines, timed_out = [], False
    p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, errors="replace", bufsize=1, start_new_session=True)
    _cur_proc["p"] = p

    def _watchdog():
        time.sleep(args.timeout)
        if p.poll() is None:
            print(f"[eval] 局超时 {args.timeout}s, kill 进程组 map={mapname}", flush=True)
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    wt = threading.Thread(target=_watchdog, daemon=True)
    wt.start()
    for line in p.stdout:
        out_lines.append(line)
        if any(k in line for k in LIVE_TAGS):
            print(f"    {line.rstrip()[:150]}", flush=True)
    p.wait()
    rc = p.returncode
    if rc == -9:      # 看门狗 SIGKILL
        timed_out, rc = True, -1
    out = "".join(out_lines)
    ev = parse_events(out)
    steps, total_r, tr_err, acts, valid, err_reason = 0, 0.0, "", [], False, ""
    try:
        with open(traj_out) as f:
            tr = json.load(f)
        steps = int(tr.get("steps", 0))
        total_r = float(tr.get("total_rew", 0.0))
        tr_err = tr.get("error", "")
        acts = tr.get("act", [])
        # 09-14 三道拦截口径: rc / traj 身份 / error
        if timed_out:
            err_reason = "timeout"
        elif rc != 0:
            err_reason = f"rc={rc}"
        elif tr.get("mapname") != mapname:
            err_reason = "traj 身份不符"
        elif tr_err:
            err_reason = f"traj.error={tr_err}"
        else:
            valid = True
    except Exception as e:
        err_reason = "timeout" if timed_out else f"no_traj:{e}"
    finally:
        if os.path.exists(traj_out):
            os.remove(traj_out)
    win = 1 if (valid and total_r >= WIN_R and 0 < steps < WIN_STEPS) else 0
    rec = {"map": mapname, "steps": steps, "r": round(total_r, 2), "win": win,
           "valid": valid, "err": err_reason, "spont": spont(acts), "rc": rc, **ev}
    results.append(rec)
    print(f"[eval] ep{i+1}/{n_ep} {mapname:<34} steps={steps:<3} r={total_r:>7.1f} "
          f"cap={ev['capture']} guard={ev['guard']} mine={ev['mine']} "
          f"spont={rec['spont']} {'VALID' if valid else 'INVALID('+err_reason+')'} "
          f"({time.time()-t0:.0f}s)", flush=True)

# --- 汇总 ---
n = len(results)
valid_rs = [r for r in results if r["valid"]]
n_valid = len(valid_rs)
n_err = n - n_valid
avg_r = sum(r["r"] for r in valid_rs) / n_valid if n_valid else 0.0
wins = sum(r["win"] for r in valid_rs)
win_rate = wins / n_valid if n_valid else 0.0

# B4 ① 正局率 (r>0 占比, valid 局中)
pos_rate = sum(1 for r in valid_rs if r["r"] > 0) / n_valid if n_valid else 0.0
# B4 ① 大负率 (r<-100 占比, valid 局中)
big_neg = sum(1 for r in valid_rs if r["r"] < B4_BIG_NEG_TH) / n_valid if n_valid else 0.0
# B4 ① GUARD 首胜率: 1v3 课程无独立"GUARD 首胜"标记 (守卫首胜+capture 双终局),
# 用"guard>0 占比"作 proxy (与 B4 L99 注 "T03 课程下以 GUARD 首胜率作 proxy" 一致);
# legacy profile 下 win_rate 即 GUARD 首胜率 (win 判据 = r>=80 & steps<60, 同 B4 L99)
guard_prime_rate = (sum(1 for r in valid_rs if r["guard"] > 0) / n_valid) if n_valid else 0.0

def grp_stats(g):
    rs = [r for r in valid_rs if group_of(r["map"]) == g]
    if not rs:
        return None
    gn = len(rs)
    return {
        "n": gn,
        "avg_r": sum(r["r"] for r in rs) / gn,
        "t200": sum(1 for r in rs if r["steps"] >= 200),
        "spont": sum(1 for r in rs if r["spont"] > 0),
        "guard": sum(1 for r in rs if r["guard"] > 0),
        "cap_eps": sum(1 for r in rs if r["capture"] > 0),
        "cap_tot": sum(r["capture"] for r in rs),
    }

print(f"\n[eval] SUMMARY profile={args.profile} ckpt_step={ckpt_step} "
      f"valid={n_valid}/{n} invalid={n_err} avg_r={avg_r:.1f}")
print(f"  {'组':<6}{'局数':>4}{'avg_r':>8}{'200步局':>10}{'自发经济':>9}{'守卫闭环':>9}{'capture局/次':>13}")
panel = {}
for g in ("1v3", "duel", "T05", "H3M"):
    s = grp_stats(g)
    if not s:
        continue
    panel[g] = s
    print(f"  {g:<6}{s['n']:>4}{s['avg_r']:>8.1f}"
          f"{s['t200']:>5}({s['t200']*100//s['n']:>3}%)"
          f"{s['spont']:>4}({s['spont']*100//s['n']:>3}%)"
          f"{s['guard']:>4}({s['guard']*100//s['n']:>3}%)"
          f"{s['cap_eps']:>6}/{s['cap_tot']:<5}")

# --- 晋级判定 ---
print()
if args.profile == "legacy":
    verdict = []
    verdict.append(f"线①GUARD 首胜率 {win_rate:.0%} {'✅' if win_rate >= PROMO_WIN_RATE else '⬜'} (≥30%)")
    verdict.append(f"线②avg_r {avg_r:.1f} {'✅' if avg_r > 0 else '⬜'} (>0)")
    verdict.append(f"线③正局率 {pos_rate:.0%} {'✅' if pos_rate >= B4_POS_RATE_MIN else '⬜'} (≥70%)")
    verdict.append(f"线④大负率 {big_neg:.0%} {'✅' if big_neg <= B4_BIG_NEG_MAX else '⬜'} (保持 0)")
    # legacy profile 无 vloss (离线 eval 不测 vloss), 五指标中 vloss 跳过
    promo = "样本不足(n<10)" if n_valid < 10 else ("达标提示(晋级需人工确认)" if win_rate >= PROMO_WIN_RATE or avg_r > 0 else "未达标")
    print(f"[eval] legacy 小图口径 (B4 五指标): {' | '.join(verdict)}  →  {promo}")
else:
    s = panel.get("1v3")
    print("[eval] 1v3 课程判据快照 (固定 ckpt 基线, 晋级线人工拍板; 在线口径见 check_win1_watch):")
    if not s:
        print("  本 profile 无 1v3 局 (用 --profile 1v3 或 all)")
    else:
        nn = s["n"]
        print(f"  样本 {nn} 局" + ("" if nn >= 3 else "  ⏳ 样本极小, 仅参考"))
        print(f"  ① capture 触发: {s['cap_tot']}次/{s['cap_eps']}局 {'✅' if s['cap_tot'] else '⬜'}")
        print(f"  ② 守卫闭环 {s['guard']*100//nn}% {'✅' if s['guard']*100 >= 80*nn else '⬜'} (≥80%)")
        print(f"  ③ 自发经济 {s['spont']*100//nn}% {'✅' if s['spont']*100 >= 80*nn else '⬜'} (≥80%)")
        print(f"  ④ 200 步局 {s['t200']*100//nn}% {'✅' if s['t200']*100 <= 20*nn else '⬜'} (≤20%)")
        print(f"  avg_r={s['avg_r']:.1f} (与上次同 profile eval 比较, 跌幅 >20% 为回退线)")

        # --- B4 双条件 PROMO_HINT (方案_B1-B4 L100: GUARD 首胜率 ≥30% AND avg_r ≥+15 连续 3 窗) ---
        # 1v3 课程下 GUARD 首胜率 proxy = guard>0 占比 (1v3 无独立 GUARD 首胜标记,
        # capture/守卫首胜双终局); 双条件用 AND (B4 L100 原文 "双条件触发晋级")
        guard_ok = guard_prime_rate >= B4_GUARD_PRIME_RATE
        avg_r_ok = avg_r >= B4_AVG_R_MIN
        print(f"\n[B4] 双条件晋级判据 (GUARD 首胜率 ≥{B4_GUARD_PRIME_RATE:.0%} AND avg_r ≥+{B4_AVG_R_MIN:.0f} 连续 {B4_AVG_R_WINDOWS} 窗):")
        print(f"  ① GUARD 首胜率 (proxy=guard>0 占比): {guard_prime_rate:.0%} {'✅' if guard_ok else '⬜'} (≥{B4_GUARD_PRIME_RATE:.0%})")
        print(f"  ② 正局率 (r>0): {pos_rate:.0%} {'✅' if pos_rate >= B4_POS_RATE_MIN else '⬜'} (≥{B4_POS_RATE_MIN:.0%})")
        print(f"  ③ avg_r: {avg_r:.1f} {'✅' if avg_r_ok else '⬜'} (≥+{B4_AVG_R_MIN:.0f})")
        print(f"  ④ 大负率 (r<-100): {big_neg:.0%} {'✅' if big_neg <= B4_BIG_NEG_MAX else '⬜'} (保持 0)")
        print(f"  ⑤ vloss: N/A (离线 eval 不测, 见 B4 L97 / 训练日志 [vloss] 字段)")

        # avg_r 连续 N 窗: 查历史 eval_history.jsonl 本 profile 同 ckpt 趋势
        windows_ok = False
        if avg_r_ok and os.path.exists(HIST):
            # 取本 profile 同 ckpt 最近 B4_AVG_R_WINDOWS 条历史 (含本次) 的 avg_r
            same_ckpt = []
            try:
                for line in reversed(open(HIST).read().strip().split("\n")):
                    try:
                        rec_h = json.loads(line)
                    except Exception:
                        continue
                    if rec_h.get("profile", "legacy") == args.profile and rec_h.get("ckpt_step") == ckpt_step:
                        same_ckpt.append(rec_h.get("avg_r", 0.0))
                        if len(same_ckpt) >= B4_AVG_R_WINDOWS:
                            break
            except Exception:
                pass
            # 历史不足 B4_AVG_R_WINDOWS 条时按实际条数判 (首跑仅 1 条 → 不触发, 需累积 3 窗)
            if len(same_ckpt) >= B4_AVG_R_WINDOWS:
                windows_ok = all(x >= B4_AVG_R_MIN for x in same_ckpt)
            else:
                print(f"  ⏳ avg_r 连续 {B4_AVG_R_WINDOWS} 窗未达: 本 ckpt 历史仅 {len(same_ckpt)} 条 "
                      f"(需累积 {B4_AVG_R_WINDOWS} 条 eval, 首跑不触发)")

        b4_pass = guard_ok and avg_r_ok and windows_ok
        if n_valid < 10:
            print(f"  → [PROMO_HINT] 样本不足 (n={n_valid}<10), 仅参考不出结论")
        elif b4_pass:
            print(f"  → [PROMO_HINT] B4 双条件达标 (GUARD {guard_prime_rate:.0%} ≥{B4_GUARD_PRIME_RATE:.0%} "
                  f"& avg_r {avg_r:.1f} ≥+{B4_AVG_R_MIN:.0f} ×{B4_AVG_R_WINDOWS}窗) — 晋级提示, 需人工确认 (B4 L100)")
        else:
            reasons = []
            if not guard_ok:
                reasons.append(f"GUARD {guard_prime_rate:.0%}<{B4_GUARD_PRIME_RATE:.0%}")
            if not avg_r_ok:
                reasons.append(f"avg_r {avg_r:.1f}<+{B4_AVG_R_MIN:.0f}")
            if avg_r_ok and not windows_ok:
                reasons.append(f"avg_r 连续 {B4_AVG_R_WINDOWS} 窗未达")
            print(f"  → B4 未达标: {', '.join(reasons)}")

# --- 历史趋势 (同 profile 上一条有效记录) ---
rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "profile": args.profile,
       "ckpt_step": ckpt_step, "n": n, "n_valid": n_valid,
       "win_rate": round(win_rate, 3), "avg_r": round(avg_r, 2),
       "b4_pos_rate": round(pos_rate, 3), "b4_big_neg": round(big_neg, 3),
       "b4_guard_prime_rate": round(guard_prime_rate, 3),
       "invalid": n_err, "panel": panel, "results": results}
os.makedirs(os.path.dirname(HIST), exist_ok=True)
with open(HIST, "a") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
if os.path.exists(HIST):
    prev_same = None
    for line in reversed(open(HIST).read().strip().split("\n")[:-1]):
        try:
            p = json.loads(line)
        except Exception:
            continue
        if p.get("profile", "legacy") == args.profile and p.get("n_valid", p.get("n", 0)):
            prev_same = p
            break
    if prev_same:
        pa = prev_same.get("panel", {})
        cur = panel.get("1v3")
        pre = pa.get("1v3")
        if cur and pre:
            ratio = cur["avg_r"] / pre["avg_r"] if abs(pre["avg_r"]) > 1e-9 else float("nan")
            tag = "✅" if ratio >= 0.8 else "⚠️回退"
            print(f"[eval] 趋势 vs 上次 {prev_same['ts']} ckpt={prev_same['ckpt_step']}: "
                  f"1v3 avg_r {pre['avg_r']:.1f}→{cur['avg_r']:.1f} (比值 {ratio:.2f} {tag}), "
                  f"capture {pre['cap_tot']}→{cur['cap_tot']}")
        else:
            print(f"[eval] 上次同 profile 记录: {prev_same['ts']} ckpt={prev_same['ckpt_step']} "
                  f"avg_r={prev_same.get('avg_r')}")
print(f"[eval] 历史已追加 {HIST}")
