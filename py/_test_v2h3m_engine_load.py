#!/usr/bin/env python3
"""_test_v2h3m_engine_load.py — 引擎侧测试反转出的 .h3m 能否被 VCMI 加载并跑几步 (#294)

在 vcmi_gym 起 StrategicEnv (mapname=h3m 前缀走 h3m 引擎路径), 引擎实际读 .h3m,
跑 N 步 obs, 不崩即证明字节镜像正确。引擎库模式, 与批跑不抢资源。
"""
import os
import sys

ROOT = "/mnt/d/Bigdata/hero3_fresh"
GYM = "/home/administrator/vcmi-workspace"

os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
sys.path.insert(0, GYM)
sys.path.insert(0, ROOT)

from vcmi_gym.envs.v13.strategic_env import StrategicEnv  # noqa: E402


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default="allforone_test.h3m", help="引擎 Maps 目录下的 h3m 文件名")
    ap.add_argument("--steps", type=int, default=30)
    args = ap.parse_args()

    env = StrategicEnv(
        mapname=args.map,
        seed=42,
        red="StupidAI",
        blue="StupidAI",
        red_adventure_ai="StupidAI",
        blue_adventure_ai="StupidAI",
        random_heroes=1,  # 测试图仅 2 家, 非 randomHeroes 模式引擎要求 >=2 非中立玩家
        boot_timeout=120,
        vcmi_timeout=900,
        vcmi_loglevel_global="error",
        vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR",
    )
    obs = env.reset()
    print(f"[ok] reset, obs shape={getattr(obs, 'shape', None)}")
    for i in range(args.steps):
        obs, r, done, info = env.step(10)  # 10 = END_TURN
        if i % 5 == 0:
            print(f"[step {i}] r={r:.1f} done={done}")
        if done:
            print(f"[done] at step {i}")
            break
    print("[ok] engine load+run passed")
    env.close()


if __name__ == "__main__":
    main()
