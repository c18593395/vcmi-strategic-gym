#!/usr/bin/env python3
"""StrategicEnv 端到端测试 — reset → step(END_TURN) → obs 返回验证

只测连通性，不修代码。shutdown crash 是已知的（下个任务修）。
"""

import sys
import os
import time
import traceback

# ---- WSL2 路径设置 ----
VCMI_REL = "/home/administrator/vcmi-workspace/vcmi/rel/bin"
CONN_REL = "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
VCMI_GYM = "/home/administrator/vcmi-workspace/vcmi_gym"

os.environ.setdefault("LD_LIBRARY_PATH", f"{VCMI_REL}:{CONN_REL}")
sys.path.insert(0, VCMI_GYM)

from vcmi_gym.envs.v13.strategic_env import StrategicEnv, END_TURN, OBS_DIM


def run_test(mapname, red, blue, label):
    """Return (name, passed, obs_nonzero_step1, obs_nonzero_step2)"""
    print(f"\n{'='*70}")
    print(f"TEST {label}: mapname={mapname}, red={red}, blue={blue}")
    print(f"{'='*70}")
    sys.stdout.flush()

    try:
        env = StrategicEnv(
            mapname=mapname,
            red=red,
            blue=blue,
            boot_timeout=120,
            random_heroes=0,
            vcmienv_loglevel="WARN",
            vcmi_loglevel_global="warn",
            vcmi_loglevel_ai="error",
            max_turns=3,
        )
        print(f"  [OK] Env created")
        sys.stdout.flush()
    except Exception as e:
        print(f"  [FAIL] Env creation: {e}")
        traceback.print_exc()
        return (label, False, 0, 0)

    # ---- reset ----
    print(f"  reset()...")
    sys.stdout.flush()
    try:
        t0 = time.time()
        obs, info = env.reset()
        t = time.time() - t0
        nonzero1 = int((obs != 0).sum())
        print(f"  [OK] reset: obs.shape={obs.shape}, nonzero={nonzero1}/{OBS_DIM}, "
              f"info={info}, time={t:.1f}s")
        print(f"        obs[:8] (global): day={obs[0]} week={obs[1]} month={obs[2]} "
              f"player={obs[3]} map={int(obs[4])}x{int(obs[5])} "
              f"underground={obs[6]} players={obs[7]}")
        sys.stdout.flush()

        if nonzero1 == 0:
            print(f"  [WARN] reset obs is ALL ZERO — StrategicState not readable")
    except Exception as e:
        print(f"  [FAIL] reset: {e}")
        traceback.print_exc()
        try: env.close()
        except: pass
        return (label, False, 0, 0)

    # ---- step(END_TURN) ----
    print(f"  step(END_TURN={END_TURN})...")
    sys.stdout.flush()
    try:
        t0 = time.time()
        obs2, reward, terminated, truncated, info2 = env.step(END_TURN)
        t = time.time() - t0
        nonzero2 = int((obs2 != 0).sum())
        print(f"  [OK] step: obs.shape={obs2.shape}, nonzero={nonzero2}/{OBS_DIM}, "
              f"reward={reward:.4f}, done={terminated or truncated}, "
              f"info={info2}, time={t:.1f}s")
        print(f"        obs[:8] (global): day={obs2[0]} week={obs2[1]} month={obs2[2]} "
              f"player={obs2[3]} map={int(obs2[4])}x{int(obs2[5])} "
              f"underground={obs2[6]} players={obs2[7]}")
        sys.stdout.flush()

        passed = nonzero2 > 0
        if not passed:
            print(f"  [FAIL] post-step obs is ALL ZERO")
    except Exception as e:
        print(f"  [FAIL] step: {e}")
        traceback.print_exc()
        try: env.close()
        except: pass
        return (label, False, nonzero1, 0)

    # ---- close (known crash expected) ----
    print(f"  close()...")
    sys.stdout.flush()
    try:
        env.close()
        print(f"  [OK] close completed cleanly")
    except Exception as e:
        print(f"  [OK] close exception (expected for strategic): {type(e).__name__}")
    sys.stdout.flush()

    return (label, passed, nonzero1, nonzero2)


# ===== Main =====
print("=" * 70)
print("StrategicEnv E2E Test")
print(f"  OBS_DIM = {OBS_DIM}")
print(f"  END_TURN = {END_TURN}")
print("=" * 70)
sys.stdout.flush()

results = []
results.append(run_test("adventure-A1.vmap", "MMAI_USER", "StupidAI",
                        "adventure-A1 + MMAI_USER"))

# Only run s1 if adventure fails (diagnostic)
# results.append(run_test("s1.vmap", "StupidAI", "StupidAI", "s1 + StupidAI"))

# Summary
print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
all_pass = True
for name, passed, nz1, nz2 in results:
    emoji = "PASS" if passed else "FAIL"
    nz_str = f"nonzero: reset={nz1}/{OBS_DIM}, step={nz2}/{OBS_DIM}"
    print(f"  [{emoji}] {name}  ({nz_str})")
    if not passed:
        all_pass = False

print(f"\n{'='*70}")
if all_pass:
    print("** ALL TESTS PASSED **")
    sys.exit(0)
else:
    print("** SOME TESTS FAILED **")
    sys.exit(1)
