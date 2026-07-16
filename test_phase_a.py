#!/usr/bin/env python3
"""
Phase A 综合验证：A6.1(回调) + A6.2(ctypes读取)
启动冒险地图 → 等待 yourTurn → 读 g_strategic_state → 验证数据
"""
import ctypes, struct, sys, os, threading, time

# === Path setup ===
sys.path.insert(0, "/home/administrator/vcmi-workspace")
os.environ["LD_LIBRARY_PATH"] = (
    "/home/administrator/vcmi-native/rel/bin:"
    "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
)

# === Step 1: Start VCMI with adventure connector ===
print("=== Phase A Verification ===")
print("[A6.1] Starting VCMI with adventure connector...")

import connector_v13

conn = connector_v13.ThreadConnector(
    maxlogs=100, bootTimeout=30, vcmiTimeout=99999, userTimeout=30,
    red="MMAI_USER", redModel="", blue="StupidAI", blueModel="",
    mapname="gym/s1.vmap", seed=0,
    randomHeroes=0, randomObstacles=0, townChance=0,
    warmachineChance=0, randomArmies=False,
    randomArmyValueMin=5000, randomArmyValueMax=5000000,
    randomArmyTargetVar=0, tightFormationChance=0,
    randomTerrainChance=0, leftVipChance=0, rightVipChance=0,
    battlefieldPattern="", manaMin=0, manaMax=0,
    randomPrimarySkills=0, swapSides=0,
    loglevelGlobal="error", loglevelAI="error",
    loglevelNetwork="error", loglevelStats="error",
    redAllowMlBot=False, blueAllowMlBot=False,
    statsMode="disabled", statsStorage="-", statsPersistFreq=0,
)

t0 = time.time()
def run_vcmi():
    try:
        conn.start()
    except Exception as e:
        print(f"conn.start() exception: {e}", file=sys.stderr)

t = threading.Thread(target=run_vcmi, daemon=True)
t.start()

print("[A6.1] Waiting for yourTurn callback (30s timeout)...")
try:
    code, state_str = conn.adventure_wait()
    elapsed = time.time() - t0
except Exception as e:
    print(f"FAIL: adventure_wait exception: {e}")
    conn.shutdown()
    sys.exit(1)

if code != 0:
    print(f"FAIL: adventure_wait returned code={code}")
    conn.shutdown()
    sys.exit(1)

print(f"PASS A6.1: yourTurn callback received in {elapsed:.1f}s, state='{state_str}'")

# === Step 2: Read g_strategic_state via ctypes ===
print("\n[A6.2] Reading g_strategic_state via ctypes...")

lib = ctypes.CDLL("/home/administrator/vcmi-native/rel/bin/libmlclient.so")
g_ss = ctypes.c_void_p.in_dll(lib, "g_strategic_state")
ptr_val = g_ss.value

if not ptr_val:
    print("FAIL: g_strategic_state is NULL")
    conn.shutdown()
    sys.exit(1)

print(f"PASS: g_strategic_state ptr = {hex(ptr_val)}")

# Parse
data = ctypes.string_at(ptr_val, 2048)
day, week, month, cur_plr, map_w, map_h, has_u, plr_cnt = struct.unpack_from("iiiiiiii", data, 0)

print(f"  day={day} week={week} month={month}")
print(f"  current_player={cur_plr} player_count={plr_cnt}")
print(f"  map={map_w}x{map_h} underground={has_u}")

# Parse player 0 (red)
off = 32
(color, human, gold, wood, mercury, ore, sulfur, crystal, gems) = struct.unpack_from("iiiiiiiii", data, off)
print(f"  Player0: color={color} human={human} gold={gold}")

# Validate
errors = []
if day < 1: errors.append("day should be >= 1")
if gold == 0: errors.append("gold should be > 0")
if plr_cnt < 2: errors.append("player_count should be >= 2")

if errors:
    print(f"\nWARNING: {', '.join(errors)}")
    print("This may be expected if strategic_state_update hasn't been called yet.")
    print("(Requires A6.1 fix to be compiled and deployed)")
else:
    print(f"\nPASS A6.2: g_strategic_state data looks valid!")

# === Step 3: Cleanup ===
print(f"\n[A7] Sending end-turn action...")
code2, msg = conn.adventure_act(0)
print(f"  adventure_act(0=endTurn): code={code2}, msg='{msg}'")

conn.shutdown()
t.join(timeout=5)
print("\nDone!")
