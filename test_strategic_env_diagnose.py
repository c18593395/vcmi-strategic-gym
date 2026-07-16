#!/usr/bin/env python3
"""StrategicEnv 诊断 — 测 reset + StrategicState 可读性，不测 step"""

import sys, os, time, ctypes, traceback

VCMI_REL = "/home/administrator/vcmi-workspace/vcmi/rel/bin"
CONN_REL = "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
VCMI_GYM = "/home/administrator/vcmi-workspace/vcmi_gym"

os.environ.setdefault("LD_LIBRARY_PATH", f"{VCMI_REL}:{CONN_REL}")
sys.path.insert(0, VCMI_GYM)

from vcmi_gym.envs.v13.strategic_env import StrategicEnv, END_TURN, OBS_DIM, _read_strategic_state, StrategicState

print("="*60)
print("Phase 1: 检查 libmlclient.so 和 g_strategic_state")
print("="*60)
sys.stdout.flush()

# Try finding the lib
lib_paths = [
    "/home/administrator/vcmi-workspace/vcmi/rel/bin/libmlclient.so",
    os.path.join(os.path.dirname(__file__) if '__file__' in dir() else '.', "vcmi/rel/bin/libmlclient.so"),
]

# Check ctypes loading
for lp in lib_paths:
    exists = os.path.exists(lp)
    print(f"  {lp}: exists={exists}")
sys.stdout.flush()

# Try direct ctypes access
try:
    libml = ctypes.CDLL("/home/administrator/vcmi-workspace/vcmi/rel/bin/libmlclient.so", use_errno=True)
    gss = ctypes.c_void_p.in_dll(libml, "g_strategic_state")
    print(f"  libml loaded OK: g_strategic_state @ {gss.value}")
    if gss.value:
        state = StrategicState.from_address(gss.value)
        print(f"  StrategicState read: day={state.day}, players={state.player_count}")
    else:
        print(f"  g_strategic_state is NULL (expected before VCMI starts)")
except Exception as e:
    print(f"  libml error: {type(e).__name__}: {e}")

print()
print("="*60)
print("Phase 2: 创建 StrategicEnv + reset")
print("="*60)
sys.stdout.flush()

env = StrategicEnv(
    mapname="adventure-A1.vmap",
    red="MMAI_USER",
    blue="StupidAI",
    boot_timeout=120,
    random_heroes=0,
    vcmienv_loglevel="WARN",
    vcmi_loglevel_global="warn",
    vcmi_loglevel_ai="error",
    max_turns=3,
)
print("  [OK] Env created")
sys.stdout.flush()

print("\n  reset()... (waiting up to 30s)")
sys.stdout.flush()
t0 = time.time()
obs, info = env.reset()
elapsed = time.time() - t0
nonzero = int((obs != 0).sum())
print(f"  [OK] reset: obs.shape={obs.shape}, nonzero={nonzero}/{OBS_DIM}, elapsed={elapsed:.1f}s")
print(f"  info: {info}")

if nonzero == 0:
    print(f"\n  *** StrategicState 未返回数据 ***")
    print(f"  检查 libmlclient.so 的 g_strategic_state 指针")
    sys.stdout.flush()
    
    # Check after reset
    try:
        state = env._last_state
        print(f"  env._last_state: {state}")
    except:
        pass

    # Try direct ctypes again after VCMI started
    try:
        libml = ctypes.CDLL("/home/administrator/vcmi-workspace/vcmi/rel/bin/libmlclient.so", use_errno=True)
        gss = ctypes.c_void_p.in_dll(libml, "g_strategic_state")
        print(f"  After reset: g_strategic_state @ {gss.value}")
        if gss.value:
            state = StrategicState.from_address(gss.value)
            print(f"  After reset state: day={state.day}, players={state.player_count}, game_over={state.game_over}")
    except Exception as e:
        print(f"  After reset ctypes error: {type(e).__name__}: {e}")

# Try step with short timeout (if reset returned)
if nonzero > 0:
    print(f"\n{'='*60}")
    print(f"Phase 3: step(END_TURN)")
    print(f"{'='*60}")
    sys.stdout.flush()
    
    # Just send and observe what happens up to the wait
    print(f"  adventure_act(0)...")
    sys.stdout.flush()
    code, msg = env.connector.adventure_act(0)
    print(f"  adventure_act result: code={code}, msg='{msg}'")
    sys.stdout.flush()
    
    if code == 0:
        print(f"  adventure_wait()... (max 60s)")
        sys.stdout.flush()
        try:
            t0 = time.time()
            # Manual wait with timeout
            import queue, threading
            result = [None]
            def do_wait():
                code2, ps = env.connector.adventure_wait()
                result[0] = (code2, ps)
            thr = threading.Thread(target=do_wait, daemon=True)
            thr.start()
            thr.join(timeout=60)
            elapsed = time.time() - t0
            if thr.is_alive():
                print(f"  [FAIL] adventure_wait timed out after {elapsed:.0f}s")
            else:
                code2, ps = result[0]
                player = int(ps) if ps else -1
                print(f"  adventure_wait OK: player={player}, time={elapsed:.1f}s")
                state2 = env._read_state()
                if state2:
                    obs2 = env._build_obs(state2)
                    nonzero2 = int((obs2 != 0).sum())
                    print(f"  Post-step obs nonzero: {nonzero2}/{OBS_DIM}")
        except Exception as e:
            print(f"  adventure_wait error: {type(e).__name__}: {e}")

print(f"\n{'='*60}")
print("close()...")
sys.stdout.flush()
try:
    env.close()
except Exception as e:
    print(f"  close exception (expected): {type(e).__name__}: {e}")

print("\nDone.")
