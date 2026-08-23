#!/usr/bin/env python3
"""地形栅格冒烟测试 — 验证坐标对齐和通道值"""
import sys, os, json
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["PYTHONPATH"] = "/mnt/d/Bigdata/hero3_fresh"

import numpy as np

# 加载 StrategicState reader
import strategic_reader as sr

def test_terrain_grid():
    """从 ep_runner 输出 JSON 读取 terrain_grid 并验证"""
    # 先用 ep_runner 跑几步, 然后读 terrain_grid
    # 这里直接测试 _build_terrain_grid 的逻辑

    # 读取一个已有的测试 JSON (如果有 terrain_grid 数据)
    json_path = "/home/administrator/test_terrain2.json"
    if not os.path.exists(json_path):
        print("SKIP: no test JSON found")
        return

    with open(json_path) as f:
        d = json.load(f)

    print(f"steps={d['steps']}, rew={d['total_rew']}")

    # terrain_grid 不在 JSON 里 (ep_runner 不保存)
    # 需要直接从 env 读取
    # 用 StrategicEnv 的 reset 获取
    from vcmi_gym.envs.v13.strategic_env import StrategicEnv

    env = StrategicEnv(
        mapname="T01_adventure_20X20_01.vmap",
        max_turns=5,
        seed=42,
    )

    try:
        obs, info = env.reset()
        tg = info.get("terrain_grid")
        if tg is None:
            print("FAIL: terrain_grid not in info")
            return

        print(f"terrain_grid shape: {tg.shape}")  # (4, 21, 21)
        print(f"terrain_grid dtype: {tg.dtype}")
        print(f"terrain_grid range: [{tg.min():.3f}, {tg.max():.3f}]")

        # Case 1: 基础对齐
        # 英雄在 (9,8) (visitablePos), 矿在 (15,15)
        # 栅格中心 (10,10) 应该是英雄位置
        # 矿相对偏移: dx=15-9=6, dy=15-8=7
        # 栅格坐标: c=10+6=16, r=10+7=17

        center_terrain = tg[0, 10, 10]  # C0 at center
        center_blocked = tg[1, 10, 10]  # C1 at center
        center_obj = tg[2, 10, 10]      # C2 at center

        print(f"\n=== Case 1: 基础对齐 ===")
        print(f"Center (10,10) C0 terrain: {center_terrain:.3f} (expect >0, hero on valid terrain)")
        print(f"Center (10,10) C1 blocked: {center_blocked:.3f} (expect 0, hero tile is passable)")
        print(f"Center (10,10) C2 object:  {center_obj:.3f} (expect 6/255=hero, or 0 if hero not counted)")

        # 矿位置 (如果在视野内)
        mine_r, mine_c = 17, 16  # (15,15) relative to hero (9,8)
        if 0 <= mine_r < 21 and 0 <= mine_c < 21:
            mine_terrain = tg[0, mine_r, mine_c]
            mine_blocked = tg[1, mine_r, mine_c]
            mine_obj = tg[2, mine_r, mine_c]
            print(f"\nMine at grid ({mine_r},{mine_c}):")
            print(f"  C0 terrain: {mine_terrain:.3f}")
            print(f"  C1 blocked: {mine_blocked:.3f}")
            print(f"  C2 object:  {mine_obj:.3f} (expect 1/255=mine)")
        else:
            print(f"\nMine at grid ({mine_r},{mine_c}): OUT OF RANGE")

        # Case 2: 边界测试
        # 如果英雄在 (9,8), 左上角 grid (0,0) = map (-1,-2) = 越界
        print(f"\n=== Case 2: 边界测试 ===")
        corner_terrain = tg[0, 0, 0]
        corner_blocked = tg[1, 0, 0]
        corner_vis = tg[3, 0, 0]
        print(f"Corner (0,0) C0 terrain: {corner_terrain:.3f} (expect 0, out of bounds)")
        print(f"Corner (0,0) C1 blocked: {corner_blocked:.3f} (expect 1/255, out of bounds = blocked)")
        print(f"Corner (0,0) C3 visible: {corner_vis:.3f} (expect 0, out of bounds)")

        # 右下角 grid (20,20) = map (9+10, 8+10) = (19,18) = 在地图内 (20x20)
        br_terrain = tg[0, 20, 20]
        br_blocked = tg[1, 20, 20]
        print(f"Bottom-right (20,20) C0 terrain: {br_terrain:.3f}")
        print(f"Bottom-right (20,20) C1 blocked: {br_blocked:.3f}")

        # 统计
        total = 21 * 21
        blocked_count = (tg[1] > 0.5).sum()
        valid_terrain = (tg[0] > 0.01).sum()
        has_obj = (tg[2] > 0.01).sum()
        print(f"\n=== 统计 ===")
        print(f"Valid terrain tiles: {valid_terrain}/{total}")
        print(f"Blocked tiles: {blocked_count}/{total}")
        print(f"Tiles with objects: {has_obj}/{total}")

        # 验证
        errors = []
        if center_blocked > 0.5:
            errors.append("FAIL: center tile should not be blocked")
        if corner_blocked < 0.5:
            errors.append("FAIL: corner (out of bounds) should be blocked")
        if corner_terrain > 0.01:
            errors.append("FAIL: corner (out of bounds) terrain should be 0")
        if valid_terrain < 100:
            errors.append(f"WARN: only {valid_terrain} valid terrain tiles (expected >100)")

        if errors:
            print(f"\nERRORS:")
            for e in errors:
                print(f"  {e}")
        else:
            print(f"\nALL CHECKS PASSED")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        env.close()

if __name__ == "__main__":
    test_terrain_grid()
