# -*- coding: utf-8 -*-
"""
probe_t06_gameover.py — T06 终局方向判别探针 (g3b 交付, 09-11 只写不跑, 错窗执行)
=======================================================================
目的: 定判 T06 局终止来源 (三选一):
  A. 300s adventure_wait 超时 forcing (strategic_env L724-736: 全零 obs + info{game_over:0, timeout:True};
     训练侧 ep_runner L330 传 vcmienv_loglevel="ERROR" 抑制了 L883 WARNING "timed out after 300s"
     与 L766 INFO "Episode done" → 超时 forcing 在 train 日志零痕迹; 本探针提升到 INFO 让它自我暴露)
  B. 真实 C++ game_over (state.game_over≠0 → terminated; C++ 规则 alive_count≤1 → game_over=last_alive+1:
     1=红胜(蓝灭), 2=蓝胜(红灭))
  C. 200 步循环截断 (双方存活, 无 terminal)

判别器 (终局 4-tuple + alive, 全部可从 step() 返回值直接读):
  - timeout=True                        → A (300s forcing, nobs 全零 → 双 alive=0)
  - go==1 或 (r_alive=1 且 b_alive=0)   → B 红胜
  - go==2 或 (r_alive=0 且 b_alive=1)   → B 蓝胜
  - trunc/循环到顶 且双 alive=1          → C 200 步截断
  - players 段: base=8, 每玩家 15 字段, alive 为第 12 个 → p0 alive=obs[19], p1 alive=obs[34]
    (1v3 图另看 p2 alive=obs[49])

保真口径 (T06 运行时 override, ep_runner L130-132, 0909 双死锁修复拍板):
  - 实际 T06 局 = move_to_force=200 (全程 forced 24) + guard_done_steps=0 (GUARD_DONE 禁用),
    非交接 spec 的 15/60。本探针:
    * --move24 = 每步直发 24 (step() docstring L708: 动作 24 = "高层移动, H.6 引擎侧解析最近目标",
      不复制 Python 侧数百行粘滞目标链, C++ fill_target_list 自行选目标) ≈ T06 全程引导 regime
    * 默认自由模式 (greedy + 与训练同款基础 mask) = 无引导 regime, 双轨覆盖 "有引导/无引导" 两种终局
  - NK2 shaping 开 (与训练 --use_nk2_shaping --nk2_shaping_scale 0.45 一致); NK2 无末步 ±200
    (_calc_reward L1057 提前 return) → 末步 r 无判别力, 只读终局 4-tuple。

执行纪律 (错窗! 避免与在训 v5 争 VCMI 资源):
  1. wsl bash -c "systemctl --user stop homm3-train-v5"
  2. wsl bash -c "cd /mnt/d/Bigdata/hero3_fresh && \
       /home/administrator/vcmi-workspace/venv/bin/python py/probe_t06_gameover.py T06_adventure_72X72_01_duel.vmap"
     同命令加 --move24 再跑一局 (duel: T06_adventure_72X72_01_duel.vmap, 1v3: T06_adventure_72X72_01.vmap, 各 1-2 局)
  3. 跑完重启: wsl bash -c "systemctl --user start homm3-train-v5"
  traj 持久落盘 py/probe_t06_traj.json (D: 盘, 避免 /tmp/EP_TRAJ pid 覆盖事故重演)
"""
import os, sys, json, time, argparse

# ---- WSL 运行时环境 (镜像 train_wsl2_ppo_v2.py L123-125, setdefault 不覆盖已设值) ----
os.environ.setdefault("STRATEGIC_STATE_LIB", "/home/administrator/vcmi-native/rel/bin/libmlclient.so")
os.environ.setdefault("LD_LIBRARY_PATH",
                      "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel")
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

PROJECT = "/mnt/d/Bigdata/hero3_fresh"
DEFAULT_MODEL = "checkpoints/wsl2_ckpt_623809.pt"  # 最新 PPO ckpt (相对项目根)


class Net(nn.Module):
    # 逐字复制 ep_runner_one.py L57-79 (obs MLP + 4ch 地形 CNN 双分支, 输出 Categorical(25)+value)
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(3464,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        # CNN branch for terrain grid (4,21,21) -> 128
        self.cnn = nn.Sequential(
            nn.Conv2d(4, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 21->10
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 10->5
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),                    # 5->5
            nn.Flatten(),                                                   # 64*5*5=1600
            nn.Linear(1600, 128), nn.ReLU()
        )
        # Merge: obs(128) + cnn(128) = 256 -> 128
        self.merge = nn.Sequential(nn.Linear(256, 128), nn.ReLU())
        self.actor, self.critic = nn.Linear(128,25), nn.Linear(128,1)
    def forward(self, x, terrain=None):
        h_obs = self.fc(x)
        if terrain is not None:
            h_cnn = self.cnn(terrain)
            h = self.merge(torch.cat([h_obs, h_cnn], dim=-1))
        else:
            h = self.merge(torch.cat([h_obs, torch.zeros_like(h_obs)], dim=-1))
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)


def load_model(path):
    """镜像 ep_runner_one.py L308-323: weights_only=True 优先 → 回退 False + "model" key → 失败 None"""
    if not path or not os.path.exists(path):
        print(f"[PROBE] model 不存在 ({path}), 无模型运行 (动作=引擎随机)", flush=True)
        return None
    m = Net()
    m.eval()
    try:
        sd = torch.load(path, map_location="cpu", weights_only=True)
        m.load_state_dict(sd, strict=False)
        print(f"[PROBE] model 加载成功 (weights_only): {path}", flush=True)
        return m
    except Exception:
        try:
            sd = torch.load(path, map_location="cpu", weights_only=False)
            m.load_state_dict(sd["model"] if "model" in sd else sd, strict=False)
            print(f"[PROBE] model 加载成功 (fallback): {path}", flush=True)
            return m
        except Exception as e:
            print(f"[PROBE] model 加载失败 ({e}), 无模型运行", flush=True)
            return None


def judge(timeout, go, term, trunc, r_alive, b_alive, loop_ended=False):
    """终局来源判定 (规则见文件头判别器)"""
    if timeout:
        return "A: 300s adventure_wait 超时 forcing (全零 obs + game_over=0 + timeout=True)"
    if go == 1 or (r_alive == 1 and b_alive == 0):
        return "B: 真实 game_over=1 红胜 (C++ alive_count<=1 → last_alive+1, 蓝灭)"
    if go == 2 or (r_alive == 0 and b_alive == 1):
        return "B: 真实 game_over=2 蓝胜 (C++ alive_count<=1 → last_alive+1, 红灭)"
    if term and go not in (0, 1, 2):
        return f"?? game_over={go} 语义未知 (需查 C++ 胜负条件表)"
    if loop_ended or trunc:
        if r_alive == 1 and b_alive == 1:
            return "C: 步预算到顶/截断, 双方存活, 无 terminal (VCMI _turn 仅在 END_TURN 时递增)"
        return f"?? go={go} term={term} trunc={trunc} r_alive={r_alive} b_alive={b_alive} 需人工复核"
    return f"?? 未判别: go={go} term={term} trunc={trunc} r_alive={r_alive} b_alive={b_alive}"


def main():
    parser = argparse.ArgumentParser(description="T06 终局方向判别探针 (错窗执行)")
    parser.add_argument("mapname", nargs="?", default="T06_adventure_72X72_01_duel.vmap",
                        help="duel=T06_adventure_72X72_01_duel.vmap / 1v3=T06_adventure_72X72_01.vmap")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="ckpt (相对项目根或绝对路径); 传空串 '' 则无模型随机动作")
    parser.add_argument("--blue_ai", default="MMAI_RANDOM",
                        help="蓝方 battle AI (镜像 T06 训练命令)")
    parser.add_argument("--blue_adventure_ai", default="MMAI",
                        help="蓝方冒险 AI (镜像 T06 训练命令)")
    parser.add_argument("--max_turns", type=int, default=200,
                        help="步预算 (镜像 ep_runner 训练 200)")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--move24", action="store_true",
                        help="每步强制 a=24 (镜像 T06 override move_to_force=200 全程引导 regime)")
    parser.add_argument("--sample", action="store_true",
                        help="Categorical.sample (镜像训练采样); 默认 greedy argmax")
    parser.add_argument("--out", default="py/probe_t06_traj.json",
                        help="traj 输出 (相对项目根 → D: 盘持久)")
    args = parser.parse_args()

    model_path = args.model if os.path.isabs(args.model) else os.path.join(PROJECT, args.model)
    out_path = args.out if os.path.isabs(args.out) else os.path.join(PROJECT, args.out)
    model = load_model(model_path) if args.model else None
    mode = "move24" if args.move24 else ("sample" if args.sample else "greedy")

    # ---- StrategicEnv 构造: 镜像 ep_runner L328-342 (T06 训练参数) ----
    # probe 专属差异:
    #  1) vcmienv_loglevel="INFO" (训练侧 "ERROR") → 让被抑制的 L766 "Episode done: turn=…, game_over=…"
    #     与 L883 "timed out after 300s" WARNING 可见, probe 自带观测
    #  2) vcmi_timeout=900 同 ep_runner L332 → fuse = min(900, 300) = 300s 实际生效
    env = StrategicEnv(
        mapname=args.mapname, max_turns=args.max_turns,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
        vcmienv_loglevel="INFO", red="StupidAI", blue=args.blue_ai,
        random_heroes=0, boot_timeout=120, vcmi_timeout=900,
        red_model_path=model_path if model else "",
        blue_model_path="",
        blue_adventure_ai=args.blue_adventure_ai,
        reward_explore=0.3,
        use_nk2_shaping=True, nk2_shaping_scale=0.45,
        seed=args.seed,
    )

    obs, info = env.reset()
    if int(np.count_nonzero(obs)) == 0:
        print(f"[PROBE][BOOT] reset 返回全零 obs (首个 YourTurn 超时 / 对局可能已结束), info={info}", flush=True)
    terrain = info.get("terrain_grid")
    traj = {"obs": [obs.tolist()], "act": [], "rew": [], "nobs": [], "done": [],
            "terrain_grid": [terrain.tolist() if terrain is not None and hasattr(terrain, "tolist") else []],
            "steps": 0, "total_rew": 0.0}
    t0 = time.time()
    terminal = None  # (terminated, truncated, game_over, timeout, r_alive, b_alive)

    for _ in range(args.max_turns):
        if args.move24:
            a = 24
        elif model is not None:
            with torch.no_grad():
                obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
                # 地形栅格 CNN 输入 (2026-08-24 修复同款): 采样端漏传 terrain → CNN 全零, 行为≠学习
                tg = traj["terrain_grid"][-1] if traj["terrain_grid"] else None
                terrain_t = (torch.tensor(np.array(tg, dtype=np.float32), dtype=torch.float32).unsqueeze(0)
                              if tg is not None and len(tg) else None)
                pi, _ = model(obs_t, terrain_t)
                logits = pi.logits[0].clone()
                # 与训练同款基础 mask (ep_runner L428-449): passable + 永久屏蔽 + 非 T04 内政关
                passable = torch.tensor(obs[3211:3219], dtype=torch.bool)
                if passable.any():
                    logits[:8][~passable] = float("-inf")
                    logits[8] = float("-inf")        # INTERACT
                    logits[9] = float("-inf")        # NEXT_HERO
                    logits[11:16] = float("-inf")    # SPLIT/MERGE
                    logits[22:24] = float("-inf")    # GARRISON/RECRUIT_HERO
                    logits[16:22] = float("-inf")    # 非 T04 内政关 (T06 训练同口径)
                    a = Categorical(logits=logits).sample().item() if args.sample else int(logits.argmax())
                else:
                    a = 10  # 僵尸旁路 (ep_runner L520-522): 8 方向全堵=英雄死亡 → END_TURN
        else:
            a = int(env.action_space.sample())

        nobs, r, done, trunc, info = env.step(a)
        traj["act"].append(a)
        traj["rew"].append(float(r))
        traj["nobs"].append(nobs.tolist())
        traj["done"].append(bool(done or trunc))
        traj["steps"] += 1
        traj["total_rew"] += float(r)
        tg2 = info.get("terrain_grid")
        traj["terrain_grid"].append(tg2.tolist() if tg2 is not None and hasattr(tg2, "tolist") else [])
        print(f"[PROBE] step={traj['steps']:3d} a={a:2d} r={r:7.2f} go={info.get('game_over', 0)} "
              f"alive19={int(nobs[19])} alive34={int(nobs[34])} term={done} trunc={trunc} "
              f"{'TIMEOUT!' if info.get('timeout') else ''}", flush=True)
        obs = nobs
        if done or trunc:
            terminal = (done, trunc, int(info.get("game_over", 0)), bool(info.get("timeout", False)),
                        int(nobs[19]), int(nobs[34]))
            break

    # ---- 终局 dump (4-tuple + alive 判别 + players 段 sanity) ----
    loop_ended = terminal is None
    if loop_ended:
        terminal = (False, False, 0, False, int(obs[19]), int(obs[34]))
    term, trunc, go, timeout, r_alive, b_alive = terminal
    players = np.asarray(obs[8:43], dtype=int)  # p0 alive=obs[19], p1 alive=obs[34], p2 alive=obs[49]
    verdict = judge(timeout, go, term, trunc, r_alive, b_alive, loop_ended)
    terminal_block = {
        "terminated": bool(term), "truncated": bool(trunc),
        "game_over": int(go), "timeout": bool(timeout),
        "red_alive_p0": r_alive, "blue_alive_p1": b_alive,
        "players_dump_obs_8_43": players.tolist(),
        "verdict": verdict, "mode": mode,
        "total_rew": round(traj["total_rew"], 2), "steps": traj["steps"],
        "secs": round(time.time() - t0, 1),
        "map": args.mapname, "model": model_path, "seed": args.seed,
    }
    traj["terminal"] = terminal_block
    with open(out_path, "w") as f:
        json.dump(traj, f, ensure_ascii=False)
        f.flush(); os.fsync(f.fileno())

    print("=" * 72)
    print(f"[PROBE][TERMINAL] map={args.mapname} mode={mode} steps={traj['steps']} "
          f"secs={terminal_block['secs']} r={traj['total_rew']:.1f}")
    print(f"[PROBE][TERMINAL] terminated={term} truncated={trunc} game_over={go} timeout={timeout}")
    print(f"[PROBE][TERMINAL] alive: red_p0={r_alive} (obs[19]) blue_p1={b_alive} (obs[34])")
    print(f"[PROBE][TERMINAL] players obs[8:43] sanity: {players.tolist()}")
    print(f"[PROBE][VERDICT] {verdict}")
    print(f"[PROBE] traj -> {out_path}", flush=True)
    try:
        env.close()
    except Exception:
        pass
    os._exit(0)


if __name__ == "__main__":
    main()
