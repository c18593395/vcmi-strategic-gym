#!/usr/bin/env python3
"""地形栅格 Case 1 & 2 最终版"""
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
            ok = (actual == expected) if op == "eq" else (actual > expected) if op == "gt" else (actual != 0) if op == "nz" else False
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
# Mine placed at (15,15), mask VVV/VAV/VVV, anchor at (1,1)
# Mine visitablePos = (16,16), grid = (17,16)
# ============================================================
case1 = [
    # 中心格 = hero
    ("Center C0 terrain > 0", 10, 10, 0, 0, "gt"),
    ("Center C1 blocked = 1 (hero)", 10, 10, 1, 1, "eq"),
    ("Center C2 object = 6 (hero)", 10, 10, 2, 6, "eq"),
    ("Center C3 visible = 1", 10, 10, 3, 1, "eq"),

    # Hero 模板占位格 — C1=1, C2=0 (对象只在 visitablePos)
    ("Hero template right C1 = 1", 10, 11, 1, 1, "eq"),
    ("Hero template above C1 = 1", 9, 10, 1, 1, "eq"),

    # 远处空地
    ("Far grass C0 > 0", 5, 5, 0, 0, "gt"),
    ("Far grass C1 = 0", 5, 5, 1, 0, "eq"),
    ("Far grass C2 = 0", 5, 5, 2, 0, "eq"),

    # 金矿 visitablePos = (16,16) -> grid[17][16]
    ("Mine visitable C0 > 0", 17, 16, 0, 0, "gt"),
    ("Mine visitable C2 = 1 (mine)", 17, 16, 2, 1, "eq"),
    ("Mine visitable C3 = 1", 17, 16, 3, 1, "eq"),

    # 金矿模板其他格 — C1=1 (被 mine 占), C2=0 (对象只在 visitable)
    ("Mine template (15,15) C1 = 1", 16, 15, 1, 1, "eq"),
]

# ============================================================
# Case 2: 边界越界
# Hero at (10,9), map 20x20
# Grid (0,0) = map (0,-1): y=-1 OOB
# ============================================================
case2 = [
    # 中心格
    ("Center C0 > 0", 10, 10, 0, 0, "gt"),
    ("Center C1 = 1", 10, 10, 1, 1, "eq"),
    ("Center C2 = 6", 10, 10, 2, 6, "eq"),

    # 越界格 — C1=1, 其余 0
    ("OOB (0,0) C0 = 0", 0, 0, 0, 0, "eq"),
    ("OOB (0,0) C1 = 1", 0, 0, 1, 1, "eq"),
    ("OOB (0,0) C2 = 0", 0, 0, 2, 0, "eq"),
    ("OOB (0,0) C3 = 0", 0, 0, 3, 0, "eq"),

    # 更多越界格
    ("OOB (0,5) C1 = 1", 0, 5, 1, 1, "eq"),
    ("OOB (5,0) C1 = 1", 5, 0, 1, 1, "eq"),

    # 边界内格
    ("Inner (15,15) C0 > 0", 15, 15, 0, 0, "gt"),
    ("Inner (15,15) C3 = 1", 15, 15, 3, 1, "eq"),
]

if __name__ == "__main__":
    run_test("T01_adventure_20X20_01.vmap", "Case 1: 基础对齐", case1)
    run_test("T01_adventure_20X20_01.vmap", "Case 2: 边界越界", case2)
