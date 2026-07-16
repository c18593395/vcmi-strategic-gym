"""Test Complete: verify the yourTurn callback triggers on the adventure map"""
import sys, os, threading, time

sys.path.insert(0, "/home/administrator/vcmi-workspace")
sys.path.insert(0, "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel")
os.environ["LD_LIBRARY_PATH"] = (
    "/home/administrator/vcmi-native/rel/bin:"
    "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
)

print("=== Full Test: Adventure yourTurn Callback ===")
print()

# Sensible defaults for constructor args
DEFAULTS = {
    "maxlogs": 100,
    "bootTimeout": 30,
    "vcmiTimeout": 99999,
    "userTimeout": 99999,
    "red": "MMAI_USER",
    "redModel": "",
    "blue": "StupidAI",
    "blueModel": "",
    "mapname": "gym/s1.vmap",
    "seed": 0,
    "randomHeroes": 0,
    "randomObstacles": 0,
    "townChance": 0,
    "warmachineChance": 0,
    "randomArmies": False,
    "randomArmyValueMin": 5000,
    "randomArmyValueMax": 5000000,
    "randomArmyTargetVar": 0,
    "tightFormationChance": 0,
    "randomTerrainChance": 0,
    "leftVipChance": 0,
    "rightVipChance": 0,
    "battlefieldPattern": "",
    "manaMin": 0,
    "manaMax": 0,
    "randomPrimarySkills": 0,
    "swapSides": 0,
    "loglevelGlobal": "warn",
    "loglevelAI": "warn",
    "loglevelNetwork": "warn",
    "loglevelStats": "warn",
    "redAllowMlBot": False,
    "blueAllowMlBot": False,
    "statsMode": "disabled",
    "statsStorage": "-",
    "statsPersistFreq": 0}

# All args via **kwargs — constructor is pybind11 keyword-friendly
import connector_v13
conn = connector_v13.ThreadConnector(**DEFAULTS)

print("Connector created")
print("Map: {}".format(DEFAULTS["mapname"]))
print("Red: {}, Blue: {}".format(
    DEFAULTS["red"], DEFAULTS["blue"]))
print()

print("Starting VCMI in background thread...")
t0result = [None]

def run_vcmi():
    try:
        conn.start()
    except Exception as e:
        t0result[0] = e

vcmi_thread = threading.Thread(target=run_vcmi, name="VCMI4Adventure", daemon=True)
vcmi_thread.start()

print("Waiting for yourTurn callback (30s timeout)...")
print()

t0 = time.time()
try:
    code, state = conn.adventure_wait()
    elapsed = time.time() - t0
except Exception as e:
    print("FAILED: adventure_wait() threw exception: {}".format(e))
    conn.shutdown()
    sys.exit(1)

print()
if code == 0:
    print("PASSED: yourTurn callback triggered!")
    print("  Return code: {} (OK)".format(code))
    print("  State: {}".format(state))
    print("  Elapsed: {:.1f}s".format(elapsed))
    print()
    print("Sending end-turn action...")
    code2, msg = conn.adventure_act(0)  # 0 = endTurn
    print("  Ack: code={}, msg={}".format(code2, msg))
    print("Your turn callback works correctly!")
elif code == 1:
    print("TIMEOUT: no yourTurn callback within 30s")
    print("Check mapname path & AAI.cpp g_adventure_cb check")
    conn.shutdown()
    sys.exit(1)
else:
    print("ERROR: unexpected return code: {}".format(code))
    conn.shutdown()
    sys.exit(1)

print()
print("Shutting down connector...")
conn.shutdown()
vcmi_thread.join(timeout=5)
print("Done!")
