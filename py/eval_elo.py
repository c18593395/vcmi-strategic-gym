#!/usr/bin/env python3
"""
ELO 评估脚本：当前模型 vs 基线（固定 AI 或另一个 checkpoint）

通过 subprocess 调 WSL python 运行 ep_runner_one.py，
红蓝轮换各打 5 局（共 10 局），每局 20 步。
输出 elo_log.json，可追加已有日志。

支持两种基线类型：
  - stupidai  (默认): 蓝方为 StupidAI（VCMI 内置弱 AI），不依赖 checkpoint 文件
  - checkpoint:      蓝方为指定的 checkpoint 模型

用法：
    # 固定 AI 基线（默认）
    python eval_elo.py --current_model /path/to/model.pt --step 2000

    # 旧 checkpoint 基线
    python eval_elo.py --current_model /path/to/model.pt --baseline_model /path/to/baseline.pt --baseline_type checkpoint --step 2000

    python eval_elo.py --current_model /path/to/model.pt --baseline_model /path/to/baseline.pt --baseline_type checkpoint --step 2000 --games 20
"""

import argparse
import datetime
import json
import os
import random
import subprocess
import sys
import tempfile

# ── WSL 环境常量 ─────────────────────────────────────────────────────────
VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py"
STEPS = 20

# 默认地图池
MAPS = [
    "Key to Victory.h3m",
    "Elbow Room.h3m",
]

# 日志路径（Windows 路径）
LOG_PATH_WIN = r"D:\Bigdata\hero3_fresh\elo_log.json"
# WSL 等价路径（用于 os.path.exists 等 POSIX 调用）
LOG_PATH_WSL = "/mnt/d/Bigdata/hero3_fresh/elo_log.json"


def run_game(mapname, red_model, blue_model, baseline_type="stupidai"):
    """跑一局，返回 (total_reward, has_error)。

    根据 baseline_type 决定蓝方行为：
      - stupidai:   蓝方为 StupidAI（固定弱 AI）
      - checkpoint: 蓝方为指定的 checkpoint 模型
    """
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = (
        "/home/administrator/vcmi-native/rel/bin:"
        "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    )
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

    # 临时轨迹文件
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        traj_path = f.name

    # 构造 subprocess 参数
    cmd = [VENV, RUNNER, str(STEPS), traj_path, mapname]
    if baseline_type == "stupidai":
        cmd.extend(["--blue_ai", "StupidAI"])
    else:
        cmd.extend(["--blue_model", blue_model])

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        proc.wait(timeout=90)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        return 0.0, True
    except Exception:
        return 0.0, True

    try:
        with open(traj_path) as f:
            d = json.load(f)
        total_rew = d.get("total_rew", 0.0)
        has_error = bool(d.get("error"))
        return total_rew, has_error
    except Exception:
        return 0.0, True
    finally:
        try:
            os.unlink(traj_path)
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="ELO evaluation: current model vs baseline"
    )
    parser.add_argument(
        "--current_model",
        required=True,
        help="Path to current model checkpoint (.pt)",
    )
    parser.add_argument(
        "--baseline_model",
        default=None,
        help="Path to baseline model checkpoint (.pt) — required when baseline_type=checkpoint",
    )
    parser.add_argument(
        "--baseline_type",
        choices=["stupidai", "checkpoint"],
        default="stupidai",
        help="Baseline opponent type: 'stupidai' (StupidAI, no file needed) or 'checkpoint' (model file)",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=0,
        help="Training step number for logging (default: 0)",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=10,
        help="Number of games (must be even, default: 10)",
    )
    parser.add_argument(
        "--maps",
        nargs="+",
        default=MAPS,
        help="Map names to use (default: %s)" % MAPS,
    )
    args = parser.parse_args()

    # 校验参数
    if args.baseline_type == "checkpoint" and not args.baseline_model:
        parser.error("--baseline_model is required when --baseline_type=checkpoint")
    if args.baseline_type == "stupidai" and args.baseline_model:
        print("Info: --baseline_model ignored when --baseline_type=stupidai", file=sys.stderr)

    n_games = args.games
    if n_games % 2 != 0:
        n_games += 1  # 确保偶数，红蓝平衡
        print(f"Warning: adjusted games to {n_games} (must be even)", file=sys.stderr)

    half = n_games // 2

    # ── 跑局 ──────────────────────────────────────────────────────────
    current_advantages = []  # 从当前模型视角的 reward（正值=当前占优）
    current_wins = 0
    baseline_wins = 0
    draws = 0

    for i in range(n_games):
        mapname = random.choice(args.maps)

        if i < half:
            # Phase 1: current=red, baseline=blue
            total_rew, has_error = run_game(
                mapname, args.current_model, args.baseline_model,
                baseline_type=args.baseline_type,
            )
            if has_error:
                print(f"  [game {i+1}/{n_games}] {mapname}: ERROR (skipped)", flush=True)
                continue
            # reward 从 P0(red)=current 视角，正值=当前占优
            current_adv = total_rew
        else:
            # Phase 2: current=blue, baseline=red
            total_rew, has_error = run_game(
                mapname, args.baseline_model, args.current_model,
                baseline_type=args.baseline_type,
            )
            if has_error:
                print(f"  [game {i+1}/{n_games}] {mapname}: ERROR (skipped)", flush=True)
                continue
            # total_rew 从 P0(red)=baseline 视角，取反得 current 视角
            current_adv = -total_rew

        current_advantages.append(current_adv)

        if current_adv > 0:
            current_wins += 1
        elif current_adv < 0:
            baseline_wins += 1
        else:
            draws += 1

        print(
            f"  [game {i+1}/{n_games}] {mapname:30s}"
            f"  total_rew={total_rew:+.1f}  current_adv={current_adv:+.1f}",
            flush=True,
        )

    # ── 汇总 ──────────────────────────────────────────────────────────
    n_completed = len(current_advantages)
    if n_completed == 0:
        print("ERROR: All games failed — no results to log", file=sys.stderr)
        return 1

    avg_reward = sum(current_advantages) / n_completed
    win_rate = current_wins / n_completed if n_completed > 0 else 0.0

    record = {
        "time": datetime.datetime.now().isoformat(),
        "step": args.step,
        "baseline_type": args.baseline_type,
        "win_rate": round(win_rate, 4),
        "avg_reward": round(avg_reward, 2),
        "current_wins": current_wins,
        "baseline_wins": baseline_wins,
        "draws": draws,
        "total_games": n_completed,
    }

    # ── 读写 elo_log.json ──────────────────────────────────────────
    log_path = LOG_PATH_WSL if os.name == "posix" else LOG_PATH_WIN
    log_records = []
    if os.path.exists(log_path):
        try:
            with open(log_path) as f:
                log_records = json.load(f)
            if not isinstance(log_records, list):
                log_records = []
        except (json.JSONDecodeError, Exception):
            log_records = []

    log_records.append(record)

    with open(log_path, "w") as f:
        json.dump(log_records, f, indent=2, ensure_ascii=False)

    # ── 终端输出 ─────────────────────────────────────────────────────
    baseline_label = (
        "StupidAI"
        if args.baseline_type == "stupidai"
        else os.path.basename(args.baseline_model)
    )
    print()
    print("=" * 60)
    print(f"  ELO Evaluation — step={args.step}")
    print(f"  current_model: {os.path.basename(args.current_model)}")
    print(f"  baseline_type: {args.baseline_type}  ({baseline_label})")
    print(f"  completed games: {n_completed}")
    print(f"  win_rate:         {win_rate:.2%}")
    print(f"  avg_reward:       {avg_reward:+.2f}  (current perspective)")
    print(f"  current_wins:     {current_wins}")
    print(f"  baseline_wins:    {baseline_wins}")
    print(f"  draws:            {draws}")
    print(f"  logged to:        {log_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
