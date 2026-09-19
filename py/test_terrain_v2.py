#!/usr/bin/env python3
"""地形栅格 Case 1 & 2 修正版"""
import sys, os, time
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["PYTHONPATH"] = "/mnt/d/Bigdata/hero3_fresh"
import numpy as np

def read_terrain_grid():
    fpath = "/home/administrator/vcmi-workspace/terrain_grid.bin"
    for _ in range(20):
        raw = np.fromfile(fpath, dtype=np.uint8, count=1764)
        if raw.shape[0] == 1764 and raw.any():
            return raw.reshape(21, 21, 4)
        time.sleep(0.1)
    return None

def run_test(mapname, test_name, checks):
    from vcmi_gym.envs.v13.strategic_env import StrategicEnv
    env = StrategicEnv(mapname=mapname, max_turns=3, seed=42)
    try:
        obs, info = env.reset()
        time.sleep(0.5)
        grid = read_terrain_grid()
        if grid is None:
            print(f"[FAIL] {test_name}: terrain_grid.bin 未找到")
            return

        print(f"\n{'='*50}")
        print(f"TEST: {test_name}")
        print(f"{'='*50}")

        passed = failed = 0
        for desc, r, c, ch, expected, op in checks:
            actual = int(grid[r, c, ch])
            ok = (actual == expected) if op == "eq" else (actual > expected) if op == "gt" else (actual in expected) if op == "in" else (actual != expected) if op == "ne" else False
            status = "PASS" if ok else "FAIL"
            passed += ok
            failed += (not ok)
            print(f"  [{status}] {desc}: grid[{r}][{c}][{ch}] = {actual} (expected {op} {expected})")

        print(f"\nResult: {passed}/{passed+failed} passed")
        if failed == 0:
            print("ALL CHECKS PASSED")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        env.close()

# ============================================================
# Case 1: 基础对齐
# Hero visitablePos = (10,9), grid center = (10,10)
# Hero 模板 VVV/VAV 占 (9,8)-(11,9), visitable = (10,9)
# 矿 at (15,15): grid offset = (15-10, 15-9) = (5,6) -> grid[16][15]
# ============================================================
case1 = [
    # 中心格 = hero visitablePos (10,9)
    ("Center C0 terrain > 0", 10, 10, 0, 0, "gt"),
    ("Center C1 blocked = 1 (hero)", 10, 10, 1, 1, "eq"),
    ("Center C2 object = 6 (hero)", 10, 10, 2, 6, "eq"),
    ("Center C3 visible = 1", 10, 10, 3, 1, "eq"),

    # Hero 模板右侧 (11,9) = grid[10][11] — 被 hero 模板占了, C1=1 正确
    ("Hero template right C1 = 1 (occupied)", 10, 11, 1, 1, "eq"),
    ("Hero template right C2 = 6 (hero)", 10, 11, 2, 6, "eq"),

    # Hero 模板上方 (10,8) = grid[9][10] — 被 hero 模板占了
    ("Hero template above C1 = 1 (occupied)", 9, 10, 1, 1, "eq"),

    # 远处空地 (5,5) = map (5,4) — 应该是普通草地
    ("Far grass C0 terrain > 0", 5, 5, 0, 0, "gt"),
    ("Far grass C1 blocked = 0", 5, 5, 1, 0, "eq"),
    ("Far grass C2 object = 0 (empty)", 5, 5, 2, 0, "eq"),

    # 金矿 (15,15): hero(10,9) -> grid offset (5,6) -> grid[16][15]
    ("Mine C0 terrain > 0", 16, 15, 0, 0, "gt"),
    ("Mine C2 object = 1 (mine)", 16, 15, 2, 1, "eq"),
    ("Mine C3 visible = 1", 16, 15, 3, 1, "eq"),
]

# ============================================================
# Case 2: 边界越界
# Hero at (10,9), map 20x20
# Grid center (10,10) = map (10,9)
# Grid (0,0) = map (10-10, 9-10) = (0,-1) -> y=-1 OOB
# Grid (0,10) = map (0,-1) -> x=0 OK, y=-1 OOB
# Grid (10,0) = map (10,-1) -> y=-1 OOB
# Grid (5,0) = map (5,-1) -> y=-1 OOB
# ============================================================
case2 = [
    # 中心格: hero
    ("Center C0 > 0", 10, 10, 0, 0, "gt"),
    ("Center C1 = 1 (hero)", 10, 10, 1, 1, "eq"),
    ("Center C2 = 6 (hero)", 10, 10, 2, 6, "eq"),

    # 越界 (0,0) = map (0,-1): y=-1 OOB
    ("OOB (0,0) C0 = 0", 0, 0, 0, 0, "eq"),
    ("OOB (0,0) C1 = 1", 0, 0, 1, 1, "eq"),
    ("OOB (0,0) C2 = 0", 0, 0, 2, 0, "eq"),
    ("OOB (0,0) C3 = 0", 0, 0, 3, 0, "eq"),

    # 越界 (0,5) = map (5,-1): y=-1 OOB
    ("OOB (0,5) C1 = 1", 0, 5, 1, 1, "eq"),
    ("OOB (0,5) C0 = 0", 0, 5, 0, 0, "eq"),

    # 越界 (5,0) = map (5,-1): y=-1 OOB
    ("OOB (5,0) C1 = 1", 5, 0, 1, 1, "eq"),
    ("OOB (5,0) C0 = 0", 5, 0, 0, 0, "eq"),

    # 边界内 (15,15) = map (15,14): 在地图内
    ("Inner (15,15) C0 > 0", 15, 15, 0, 0, "gt"),
    ("Inner (15,15) C3 = 1", 15, 15, 3, 1, "eq"),
]

if __name__ == "__main__":
    run_test("T01_adventure_20X20_01.vmap", "Case 1: 基础对齐", case1)
    print("\n" + "="*50)
    run_test("T01_adventure_20X20_01.vmap", "Case 2: 边界越界", case2)
