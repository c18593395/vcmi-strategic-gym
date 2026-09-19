#!/usr/bin/env python3
"""地形栅格冒烟测试 Case 1 & Case 2"""
import sys, os, time
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["PYTHONPATH"] = "/mnt/d/Bigdata/hero3_fresh"
import numpy as np

# 直接从文件读取 (绕过 env 的时序问题)
def read_terrain_grid():
    fpath = "/home/administrator/vcmi-workspace/terrain_grid.bin"
    for _ in range(20):
        raw = np.fromfile(fpath, dtype=np.uint8, count=1764)
        if raw.shape[0] == 1764 and raw.any():
            return raw.reshape(21, 21, 4)  # HWC
        time.sleep(0.1)
    return None

def run_test(mapname, hero_pos, test_name, checks):
    """启动 env, 读取 terrain_grid, 执行 checks"""
    from vcmi_gym.envs.v13.strategic_env import StrategicEnv
    env = StrategicEnv(mapname=mapname, max_turns=3, seed=42)
    try:
        obs, info = env.reset()
        time.sleep(0.5)  # 等文件写入
        grid = read_terrain_grid()
        if grid is None:
            print(f"[FAIL] {test_name}: terrain_grid.bin 未找到或为空")
            return

        print(f"\n{'='*50}")
        print(f"TEST: {test_name}")
        print(f"Map: {mapname}, Hero expected: {hero_pos}")
        print(f"Grid shape: {grid.shape}, non-zero: {np.count_nonzero(grid)}")
        print(f"{'='*50}")

        passed = 0
        failed = 0
        for desc, r, c, ch, expected, op in checks:
            actual = int(grid[r, c, ch])
            if op == "eq":
                ok = actual == expected
            elif op == "ne":
                ok = actual != expected
            elif op == "gt":
                ok = actual > expected
            elif op == "in":
                ok = actual in expected
            else:
                ok = False

            status = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            else:
                failed += 1
            print(f"  [{status}] {desc}: grid[{r}][{c}][{ch}] = {actual} (expected {op} {expected})")

        print(f"\nResult: {passed} passed, {failed} failed")
        if failed == 0:
            print("ALL CHECKS PASSED")
    except Exception as e:
        print(f"[ERROR] {test_name}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        env.close()

# ============================================================
# Case 1: 基础对齐测试
# 用 T01_adventure_20X20_01 (hero at 9,8, mine at 15,15)
# ============================================================
# Hero at (9,8), grid center (10,10) = map (9,8)
# Mine at (15,15), grid pos: c = 10+(15-9)=16, r = 10+(15-8)=17
# Grid[10][10] = hero position
# Grid[17][16] = mine position

case1_checks = [
    # (description, row, col, channel, expected, operator)
    # 中心格: 英雄位置
    ("Center C0 terrain > 0 (hero on valid terrain)", 10, 10, 0, 0, "gt"),
    ("Center C1 blocked = 1 (hero blocks tile)", 10, 10, 1, 1, "eq"),
    ("Center C2 object = 6 (hero)", 10, 10, 2, 6, "eq"),
    ("Center C3 visible = 1", 10, 10, 3, 1, "eq"),

    # 右侧相邻格 (10,11) = map (10,8) — 应该是普通草地
    ("Right neighbor C1 blocked = 0 (passable grass)", 10, 11, 1, 0, "eq"),
    ("Right neighbor C3 visible = 1", 10, 11, 3, 1, "eq"),

    # 金矿位置 (17,16) = map (15,15)
    ("Mine C0 terrain > 0", 17, 16, 0, 0, "gt"),
    ("Mine C2 object = 1 (mine)", 17, 16, 2, 1, "eq"),
    ("Mine C3 visible = 1", 17, 16, 3, 1, "eq"),

    # 统计
    ("Total non-zero C2 objects > 0", -1, -1, -1, 0, "special"),
]

# ============================================================
# Case 2: 边界越界测试
# Hero at (9,8), map 20x20
# Grid extends from map (-1,-2) to (19,18)
# Grid (0,0) = map (-1,-2) = OUT OF BOUNDS
# ============================================================

case2_checks = [
    # 中心格: 英雄位置 (同 Case 1)
    ("Center C0 terrain > 0", 10, 10, 0, 0, "gt"),
    ("Center C1 blocked = 1 (hero)", 10, 10, 1, 1, "eq"),
    ("Center C2 object = 6 (hero)", 10, 10, 2, 6, "eq"),

    # 越界格 (0,0) = map (-1,-2) — 应该全部为 0 除了 C1=1
    ("OOB (0,0) C0 terrain = 0", 0, 0, 0, 0, "eq"),
    ("OOB (0,0) C1 blocked = 1", 0, 0, 1, 1, "eq"),
    ("OOB (0,0) C2 object = 0", 0, 0, 2, 0, "eq"),
    ("OOB (0,0) C3 visible = 0", 0, 0, 3, 0, "eq"),

    # 越界格 (0,5) = map (-1,3) — 也是越界 (x=-1)
    ("OOB (0,5) C1 blocked = 1", 0, 5, 1, 1, "eq"),
    ("OOB (0,5) C0 terrain = 0", 0, 5, 0, 0, "eq"),

    # 越界格 (5,0) = map (4,-2) — 越界 (y=-2)
    ("OOB (5,0) C1 blocked = 1", 5, 0, 1, 1, "eq"),
    ("OOB (5,0) C0 terrain = 0", 5, 0, 0, 0, "eq"),

    # 边界内格 (10,0) = map (9,-2) — y=-2 越界
    ("Edge (10,0) C1 blocked = 1 (y=-2 OOB)", 10, 0, 1, 1, "eq"),

    # 边界内格 (0,10) = map (-1,8) — x=-1 越界
    ("Edge (0,10) C1 blocked = 1 (x=-1 OOB)", 0, 10, 1, 1, "eq"),

    # 右下角 (20,20) = map (19,18) — 在地图内
    ("Bottom-right (20,20) C0 terrain > 0", 20, 20, 0, 0, "gt"),
    ("Bottom-right (20,20) C1 blocked = 0", 20, 20, 1, 0, "eq"),
]

if __name__ == "__main__":
    # Run Case 1
    run_test("T01_adventure_20X20_01.vmap", (9, 8), "Case 1: 基础对齐", case1_checks)

    print("\n" + "="*50)

    # Run Case 2 (same map, same hero position)
    run_test("T01_adventure_20X20_01.vmap", (9, 8), "Case 2: 边界越界", case2_checks)
