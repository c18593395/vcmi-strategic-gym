"""A7: Adventure test with randomHeroes=1 on Island of Fire"""
import sys, os, threading, time

sys.path.insert(0, "/home/administrator/vcmi-workspace")
os.environ["LD_LIBRARY_PATH"] = (
    "/home/administrator/vcmi-native/rel/bin:"
    "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
)

import connector_v13

print("=== A7: randomHeroes=1 adventure test ===")
print("Map: Island of Fire (adventure-island-fire.h3m)")

conn = connector_v13.ThreadConnector(
    maxlogs=500, bootTimeout=30, vcmiTimeout=99999, userTimeout=30,
    red="MMAI_USER", redModel="", blue="StupidAI", blueModel="",
    mapname="adventure-island-fire.h3m", seed=0,
    randomHeroes=1, randomObstacles=0, townChance=0,
    warmachineChance=0, randomArmies=False,
    randomArmyValueMin=5000, randomArmyValueMax=5000000,
    randomArmyTargetVar=0, tightFormationChance=0,
    randomTerrainChance=0, leftVipChance=0, rightVipChance=0,
    battlefieldPattern="", manaMin=0, manaMax=0,
    randomPrimarySkills=0, swapSides=0,
    loglevelGlobal="warn", loglevelAI="warn",
    loglevelNetwork="warn", loglevelStats="warn",
    redAllowMlBot=False, blueAllowMlBot=False,
    statsMode="disabled", statsStorage="-", statsPersistFreq=0,
)

def run_vcmi():
    try:
        conn.start()
    except Exception as e:
        print(f"start() exception: {e}", file=sys.stderr)

t = threading.Thread(target=run_vcmi, daemon=True)
t.start()

print("Waiting for yourTurn callback (60s timeout)...")
t0 = time.time()
try:
    code, state = conn.adventure_wait()
    elapsed = time.time() - t0
except Exception as e:
    print(f"FAIL: adventure_wait exception: {e}")
    conn.shutdown()
    sys.exit(1)

if code != 0:
    print(f"FAIL: adventure_wait returned code={code}")
    conn.shutdown()
    sys.exit(1)

print(f"\n✅ PASS: yourTurn received in {elapsed:.1f}s")
print(f"  State: {state}")

# ctypes read
import ctypes
lib = ctypes.CDLL("/home/administrator/vcmi-native/rel/bin/libmlclient.so")
g_ss = ctypes.c_void_p.in_dll(lib, "g_strategic_state")
print(f"  g_strategic_state: {hex(g_ss.value) if g_ss.value else 'NULL'}")

if g_ss.value:
    import struct
    data = ctypes.string_at(g_ss.value, 128)
    day, week, month, cur_plr, mw, mh, ug, pc = struct.unpack_from("iiiiiiii", data)
    print(f"  day={day} week={week} month={month} cur_player={cur_plr}")
    print(f"  map={mw}x{mh} underground={ug} players={pc}")

# Send end-turn
print("\nSending end-turn action...")
code2, msg = conn.adventure_act(0)
print(f"  adventure_act(0=endTurn): code={code2} msg={msg}")

conn.shutdown()
t.join(timeout=5)
print("\n=== A7 TEST COMPLETE ===")
