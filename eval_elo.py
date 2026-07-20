#!/usr/bin/env python3
"""
ELO 评估脚本：当前模型 vs 基准模型（最早 checkpoint）

通过 subprocess 调 WSL python 运行 ep_runner_one.py，
红蓝轮换各打 5 局（共 10 局），每局 20 步。
输出 elo_log.json，可追加已有日志。

用法：
    python eval_elo.py --current_model /path/to/model.pt --baseline_model /path/to/baseline.pt --step 2000
    python eval_elo.py --current_model /path/to/model.pt --baseline_model /path/to/baseline.pt --step 2000 --games 20
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
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
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


def run_game(mapname, red_model, blue_model):
    """跑一局，返回 (total_reward, has_error)。

    当前 ep_runner_one.py hardcode 红蓝均为 MMAI_USER（随机动作）。
    评估时通过设置 env 变量覆盖模型路径（待后续实现 C++ ML 库的 env var 支持）。
    """
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = (
        "/home/administrator/vcmi-native/rel/bin:"
        "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    )
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    # TODO: future — set model-path env vars (e.g. env["MMAI_RED_MODEL"] = red_model)
    # 当 ep_runner_one.py / StrategicEnv 支持从 env 读取红蓝模型路径时取消注释

    # 临时轨迹文件
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        traj_path = f.name

    try:
        proc = subprocess.Popen(
            [VENV, RUNNER, str(STEPS), traj_path, mapname],
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
        description="ELO evaluation: current model vs baseline model"
    )
    parser.add_argument(
        "--current_model",
        required=True,
        help="Path to current model checkpoint (.pt)",
    )
    parser.add_argument(
        "--baseline_model",
        required=True,
        help="Path to baseline model checkpoint (.pt)",
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
                mapname, args.current_model, args.baseline_model
            )
            if has_error:
                print(f"  [game {i+1}/{n_games}] {mapname}: ERROR (skipped)", flush=True)
                continue
            # reward 从 P0(red)=current 视角，正值=当前占优
            current_adv = total_rew
        else:
            # Phase 2: current=blue, baseline=red
            total_rew, has_error = run_game(
                mapname, args.baseline_model, args.current_model
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
    print()
    print("=" * 60)
    print(f"  ELO Evaluation — step={args.step}")
    print(f"  current_model: {args.current_model}")
    print(f"  baseline_model: {args.baseline_model}")
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
