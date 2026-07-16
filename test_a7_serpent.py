"""A7: Serpents Treasure adventure test"""
import sys, os, threading, time, ctypes

sys.path.insert(0, "/home/administrator/vcmi-workspace")
os.environ["LD_LIBRARY_PATH"] = (
    "/home/administrator/vcmi-native/rel/bin:"
    "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
)

import connector_v13

print("=== A7: Serpents Treasure adventure test ===")
print("Map: adventure-serpent.h3m (Serpents Treasure.h3m)")
sys.stdout.flush()

conn = connector_v13.ThreadConnector(
    maxlogs=500, bootTimeout=30, vcmiTimeout=99999, userTimeout=30,
    red="MMAI_USER", redModel="", blue="StupidAI", blueModel="",
    mapname="adventure-serpent.h3m", seed=0,
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
    try: conn.start()
    except Exception as e: print(f"start() exception: {e}", file=sys.stderr)

t = threading.Thread(target=run_vcmi, daemon=True)
t.start()
time.sleep(3)

print("Calling connect(0)...")
sys.stdout.flush()
try:
    r = conn.connect(0)
    print(f"  connect(0) returned: {r}")
except Exception as e:
    print(f"  connect(0) exception: {e}")

print("Calling adventure_wait()...")
sys.stdout.flush()
try:
    code, state = conn.adventure_wait()
    print(f"  adventure_wait: code={code} state='{state}'")
    if code == 0:
        print("  ✅ PASS: yourTurn callback received!")
except Exception as e:
    print(f"  adventure_wait exception: {e}")

conn.shutdown()
t.join(timeout=5)
print("=== A7 TEST END ===")
