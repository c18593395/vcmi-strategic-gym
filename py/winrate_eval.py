#!/usr/bin/env python3
"""WSL2 新架构模型 WIN RATE 评测 (3464 维 obs + 4x21x21 terrain, 25 动作, 自定义 Net).

与 train_wsl2_ppo_v2.py 的 Net 完全一致; 与 ep_runner_one.py 的 env 构造 + 动作屏蔽逻辑完全一致.
红方 = 待测模型 (Python 驱动 _send_action), 蓝方 = 固定 baseline (默认 MMAI_RANDOM), 统计 RED 胜率.

用法:
  python3 winrate_eval.py --model <ckpt.pt> [--maps T05_36X36_01.vmap,T06_72X72_01_duel.vmap,...]
                           [--games 8] [--blue MMAI_RANDOM] [--max_turns 250] [--out result.json]

说明:
  - 服务器 (172.16.2.40) 的 .so 是 ARM64 旧架构 (256 维), 无法跑本模型评测, 故 WIN RATE 必须在 WSL2 跑, 结果回传服务器.
  - 评测与训练共用 VCMI 引擎, 建议错峰或单跑, 避免端口/资源争用 (见 README).
  - 动作屏蔽沿用训练真源: 0-7 受 passability 约束, 8/9/11-15/22/23 永久屏蔽, 16-21 仅 T04 地图开启; 确定性 argmax.
"""
import argparse
import os
import sys
import json
import time
import traceback

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical

# ---- 候选导入路径 (vcmi_gym 装在 WSL workspace venv) ----
for _p in ("/home/administrator/vcmi-workspace", "/mnt/d/Bigdata/hero3_fresh"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from vcmi_gym.envs.v13.strategic_env import StrategicEnv  # noqa: E402

OBS_DIM = 3464
TERRAIN_CHANNELS = 4
TERRAIN_SIZE = 21


class Net(nn.Module):
    """必须与 train_wsl2_ppo_v2.py 的 Net 完全一致."""
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(3464, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.cnn = nn.Sequential(
            nn.Conv2d(4, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
            nn.Flatten(),
            nn.Linear(1600, 128), nn.ReLU()
        )
        self.merge = nn.Sequential(nn.Linear(256, 128), nn.ReLU())
        self.actor, self.critic = nn.Linear(128, 25), nn.Linear(128, 1)

    def forward(self, x, terrain=None):
        h_obs = self.fc(x)
        if terrain is not None:
            h_cnn = self.cnn(terrain)
            h = self.merge(torch.cat([h_obs, h_cnn], dim=-1))
        else:
            h = self.merge(torch.cat([h_obs, torch.zeros_like(h_obs)], dim=-1))
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)


def load_net(path):
    sd = torch.load(path, map_location="cpu", weights_only=True)
    net = Net()
    missing, unexpected = net.load_state_dict(sd, strict=True)
    net.eval()
    print(f"[winrate] loaded {path} (strict OK)", flush=True)
    return net


def masked_argmax(logits, obs, mapname):
    """沿用 ep_runner_one 训练真源的动作屏蔽; 确定性 argmax."""
    logits = logits.astype(np.float64).copy()
    passable = np.array(obs[3211:3219], dtype=bool)
    if passable.any():
        logits[:8][~passable] = -np.inf
    # 永久屏蔽: 8=INTERACT / 9=NEXT_HERO / 11-15=SPLIT/MERGE (VCMI 真源无执行分支, NOOP 刷步)
    logits[8] = -np.inf
    logits[9] = -np.inf
    logits[11:16] = -np.inf
    # 22=GARRISON / 23=RECRUIT_HERO 永久关
    logits[22:24] = -np.inf
    # 16-21 内政动作: 仅 T04 地图开启, 其余 (T05/T06/官方图) 屏蔽
    if not mapname.startswith("T04"):
        logits[16:22] = -np.inf
    if not np.isfinite(logits).any():
        return 10  # 全屏蔽兜底: 结束回合
    return int(np.argmax(logits))


def make_env(mapname, blue, max_turns, blue_adventure_ai):
    return StrategicEnv(
        mapname=mapname, max_turns=max_turns,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR", red="StupidAI", blue=blue,
        random_heroes=0, boot_timeout=120, vcmi_timeout=900,
        red_model_path="", blue_model_path="", blue_adventure_ai=blue_adventure_ai,
        reward_explore=0.0, use_nk2_shaping=False, nk2_shaping_scale=1.0,
        random_armies=False, random_army_min=500, random_army_max=1000,
    )


def play_one(env, net, mapname, max_turns):
    obs, info = env.reset()
    tg = info.get("terrain_grid")
    for _ in range(max_turns):
        with torch.no_grad():
            obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            terrain_t = (torch.tensor(np.array(tg, dtype=np.float32)).unsqueeze(0)
                         if tg is not None and len(tg) else None)
            pi, _ = net(obs_t, terrain_t)
            logits = pi.logits[0].clone().numpy()
        a = masked_argmax(logits, obs, mapname)
        obs, r, done, trunc, info = env.step(a)
        tg = info.get("terrain_grid")
        if done or trunc:
            break
    return int(info.get("game_over", 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="待测模型 .pt (state_dict, 与 Net 一致)")
    ap.add_argument("--maps", default="T05_adventure_36X36_01.vmap,T06_adventure_72X72_01_duel.vmap,King_of_Pain_h3m.vmap",
                    help="逗号分隔的地图 basename (位于 maps/training/)")
    ap.add_argument("--games", type=int, default=8, help="每图局数")
    ap.add_argument("--blue", default="MMAI_RANDOM", help="蓝方 baseline AI")
    ap.add_argument("--blue_adventure_ai", default="MMAI")
    ap.add_argument("--max_turns", type=int, default=250)
    ap.add_argument("--out", default="", help="输出 JSON 路径 (默认打印)")
    args = ap.parse_args()

    net = load_net(args.model)
    maps = [m.strip() for m in args.maps.split(",") if m.strip()]

    per_map = {}
    wins = losses = draws = errors = games_total = 0
    t0 = time.time()
    for m in maps:
        mw = ml = md = me = 0
        env = None
        try:
            env = make_env(m, args.blue, args.max_turns, args.blue_adventure_ai)
            for g in range(args.games):
                try:
                    go = play_one(env, net, m, args.max_turns)
                    if go == 1:
                        mw += 1
                    elif go == 2:
                        ml += 1
                    else:
                        md += 1
                except Exception as e:
                    me += 1
                    print(f"  [ERR] map={m} game={g}: {e}", flush=True)
                    traceback.print_exc()
                    # 重建 env 继续本图剩余局
                    try:
                        if env is not None:
                            env.close()
                    except Exception:
                        pass
                    env = make_env(m, args.blue, args.max_turns, args.blue_adventure_ai)
            if env is not None:
                env.close()
        except Exception as e:
            me += args.games
            print(f"  [FATAL] map={m}: {e}", flush=True)
            traceback.print_exc()
            if env is not None:
                try:
                    env.close()
                except Exception:
                    pass
        valid = mw + ml + md
        wr = round(mw / valid * 100, 1) if valid > 0 else 0.0
        per_map[m] = {"games": mw + ml + md + me, "wins": mw, "losses": ml,
                      "draws": md, "errors": me, "win_rate": wr}
        wins += mw; losses += ml; draws += md; errors += me
        print(f"  map={m} W={mw} L={ml} D={md} E={me} WR={wr}%", flush=True)

    games_total = wins + losses + draws + errors
    valid_total = wins + losses + draws
    overall_wr = round(wins / valid_total * 100, 1) if valid_total > 0 else 0.0
    result = {
        "model": os.path.basename(args.model),
        "blue": args.blue,
        "maps": maps,
        "games_per_map": args.games,
        "total_games": games_total,
        "wins": wins, "losses": losses, "draws": draws, "errors": errors,
        "valid_games": valid_total,
        "win_rate": overall_wr,
        "per_map": per_map,
        "elapsed_s": round(time.time() - t0, 1),
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[winrate] wrote {args.out}", flush=True)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[winrate] OVERALL: W={wins} L={losses} D={draws} E={errors} WR={overall_wr}%", flush=True)


if __name__ == "__main__":
    main()
