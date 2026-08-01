#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C8.3 BC 数据采集 — red=Nullkiller2 自主行动, 每个决策点阻塞采集 (obs, action)

协议 (strategic_state.cpp adventure_capture_turn):
  NK2 决策点(moveHeroToTile/endTurn) → C++ 填 obs + 记录 NK2 action → 阻塞
  Python: adventure_wait_for_turn() → 读 obs + adventure_get_action() → 保存 → send_action(0) 释放

动作空间 (N_ACTIONS=11): 0-7 移动方向(N-start CW), 8 交互, 9 切英雄, 10 END_TURN
每局跑在独立子进程（NK2 卡死局自动跳过，close 崩溃不中断主流程）。
输出: <out>_ep{N}.npz, 每局一个文件（C8.4 训练直接 glob 加载）。
"""
import os
import sys
import time
import argparse
import subprocess
import numpy as np

sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv, END_TURN


def run_episode(ep: int, args) -> int:
    """跑单局采集, 返回采集对数"""
    out_file = args.out.replace(".npz", f"_ep{ep}.npz")
    env = StrategicEnv(
        mapname=args.map, max_turns=999,
        red="StupidAI", blue="StupidAI",
        red_adventure_ai="Nullkiller2", blue_adventure_ai="MMAI",
        boot_timeout=args.boot_timeout, vcmi_timeout=args.vcmi_timeout,
        user_timeout=120, seed=1000 + ep,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    )
    obs_list, act_list, day_list = [], [], []
    obs0, info = env.reset()
    if info.get("day", 0) <= 0:
        print(f"[ep{ep}] RESET TIMEOUT, skip")
        try:
            env.close()
        except Exception:
            pass
        return 0

    state = env._read_state()
    act0 = env._libml.adventure_get_action()
    day0 = state.day if state else 1
    obs_list.append(obs0)
    act_list.append(act0)
    day_list.append(day0)
    env._send_action(0)  # 释放 NK2 第一个决策
    pairs = 1
    print(f"[ep{ep}] reset OK day={day0} act={act0} obs_nz={(obs0 > 0).sum()}")

    while pairs < args.max_pairs:
        try:
            env._adventure_wait(timeout=args.wait_timeout)
        except RuntimeError:
            st = env._read_state()
            if st:
                print(f"[ep{ep}] WAIT TIMEOUT state: day={st.day} current_player={st.current_player} "
                      f"game_over={st.game_over} hero0=({st.heroes[0].pos_x},{st.heroes[0].pos_y})")
            print(f"[ep{ep}] NK2 stuck, stop at {pairs} pairs")
            break
        state = env._read_state()
        obs = env._build_obs(state)
        act = env._libml.adventure_get_action()
        day = state.day if state else 0
        obs_list.append(obs)
        act_list.append(act)
        day_list.append(day)
        env._send_action(0)
        pairs += 1
        if pairs % 100 == 0:
            print(f"[ep{ep}] {pairs} pairs day={day} last_act={act}")
        if state and state.game_over:
            print(f"[ep{ep}] GAME_OVER={state.game_over} at {pairs} pairs")
            break

    if obs_list:
        obs = np.array(obs_list, dtype=np.float32)
        acts = np.array(act_list, dtype=np.int64)
        days = np.array(day_list, dtype=np.int64)
        eps = np.full(len(obs), ep, dtype=np.int64)
        np.savez(out_file, obs=obs, actions=acts, days=days, episodes=eps)
        uniq, cnts = np.unique(acts, return_counts=True)
        print(f"[ep{ep}] SAVED {len(obs)} pairs -> {out_file}")
        print(f"[ep{ep}] action 分布:", {int(k): int(v) for k, v in zip(uniq, cnts)})
    try:
        env.close()
    except Exception:
        pass
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default="Dungeon Keeper.h3m",
                    help="地图名, 用 | 分隔多图轮换 (地图名可能含逗号, 不能用逗号分隔)")
    ap.add_argument("--episodes", type=int, default=10)
    ap.add_argument("--max_pairs", type=int, default=2000, help="每局最多采集对")
    ap.add_argument("--out", default="/mnt/d/Bigdata/hero3_fresh/bc_data/bc_raw.npz")
    ap.add_argument("--boot_timeout", type=int, default=240)
    ap.add_argument("--vcmi_timeout", type=int, default=240)
    ap.add_argument("--wait_timeout", type=int, default=90, help="单步等待秒数")
    ap.add_argument("--watchdog", type=int, default=900,
                    help="整局硬超时(秒), 超时 kill 子进程跳局 (NK2 启动阶段卡死兜底)")
    ap.add_argument("--episode", type=int, default=-1, help="单局模式: 只跑这一局 (子进程用)")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    if args.episode >= 0:
        run_episode(args.episode, args)
        os._exit(0)  # 绕开 connector shutdown 崩溃

    # 主模式: 每局一个子进程（隔离崩溃）—— 地图名可能含逗号, 用 | 分隔
    maps = [m.strip() for m in args.map.split("|") if m.strip()]
    total = 0
    for ep in range(args.episodes):
        cur_map = maps[ep % len(maps)]
        cmd = [sys.executable, "-u", os.path.abspath(__file__),
               "--episode", str(ep), "--map", cur_map,
               "--max_pairs", str(args.max_pairs),
               "--out", args.out,
               "--boot_timeout", str(args.boot_timeout),
               "--vcmi_timeout", str(args.vcmi_timeout),
               "--wait_timeout", str(args.wait_timeout)]
        print(f"=== 启动局 {ep} ({cur_map}) ===")
        try:
            r = subprocess.run(cmd, cwd="/home/administrator/vcmi-workspace",
                               timeout=args.watchdog)
        except subprocess.TimeoutExpired:
            print(f"[!] 局 {ep} ({cur_map}) 超过 {args.watchdog}s 无产出, "
                  f"判定卡死, kill 跳过")
            continue
        f = args.out.replace(".npz", f"_ep{ep}.npz")
        if os.path.exists(f):
            d = np.load(f)
            total += len(d["obs"])
            print(f"局 {ep} 完成: {len(d['obs'])} pairs (累计 {total})")
        else:
            print(f"局 {ep} 无产出")
        time.sleep(3)
    print(f"TOTAL {total} pairs across {args.episodes} episodes")


if __name__ == "__main__":
    main()
