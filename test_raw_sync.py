"""Raw sync — both MMAI_USER"""
import sys, os, time, ctypes, threading
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
from vcmi_gym.connectors.rel import connector_v13

conn = connector_v13.ThreadConnector(
    maxlogs=100, bootTimeout=60, vcmiTimeout=99999, userTimeout=99999,
    red="MMAI_USER", redModel="", blue="MMAI_USER", blueModel="",
    mapname="adventure-A1.vmap", seed=0, randomHeroes=0,
    randomObstacles=0, townChance=0, warmachineChance=0,
    randomArmies=False, randomArmyValueMin=500, randomArmyValueMax=1000,
    randomArmyTargetVar=0, tightFormationChance=0, randomTerrainChance=0,
    leftVipChance=0, rightVipChance=0, battlefieldPattern="",
    manaMin=0, manaMax=0, randomPrimarySkills=0, swapSides=0,
    loglevelGlobal="error", loglevelAI="error", loglevelNetwork="error",
    loglevelStats="error", redAllowMlBot=False, blueAllowMlBot=False,
    statsMode="disabled", statsStorage="-", statsPersistFreq=100,
)

vcmithread = threading.Thread(target=conn.start, daemon=True)
vcmithread.start()
time.sleep(5)
print("VCMI started")

libml = ctypes.CDLL(os.environ["STRATEGIC_STATE_LIB"])
libml.adventure_wait_for_turn.restype = ctypes.c_int

for i in range(6):
    print(f"WAIT {i+1}")
    t0=time.time()
    p=libml.adventure_wait_for_turn()
    dt=time.time()-t0
    print(f"  GOT p={p} dt={dt:.1f}s")
    libml.adventure_send_action(10) # END_TURN
    if dt > 10:
        print("  SLOW!")
        break

print("CLOSE")
conn.shutdown()
print("PASS")
