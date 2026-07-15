import sys, os, time, threading

sys.path.insert(0, "/home/administrator/vcmi-workspace")
from connector_v13 import ThreadConnector

print("Creating ThreadConnector with StupidAI...")
conn = ThreadConnector(
    red="MMAI_USER", redModel="",
    blue="StupidAI", blueModel="",
    mapname="gym/A1.vmap",
    maxlogs=500, bootTimeout=30, vcmiTimeout=10, userTimeout=10,
    seed=0, randomHeroes=0, randomObstacles=0, townChance=0,
    warmachineChance=0, randomArmies=False, randomArmyValueMin=5000,
    randomArmyValueMax=5000000, randomArmyTargetVar=30,
    tightFormationChance=0, randomTerrainChance=0,
    leftVipChance=0, rightVipChance=0, battlefieldPattern="",
    manaMin=0, manaMax=0, randomPrimarySkills=0, swapSides=0,
    loglevelGlobal="error", loglevelAI="error", loglevelNetwork="error",
    loglevelStats="error", redAllowMlBot=False, blueAllowMlBot=True,
    statsMode="disabled", statsStorage="-", statsPersistFreq=100,
)
print("Connector created.")

t0 = time.time()

def run_vcmi():
    print("Thread: calling conn.start()...")
    conn.start()
    print("Thread: conn.start() returned")

t = threading.Thread(target=run_vcmi, daemon=True)
t.start()

print("Waiting 3s for VCMI init...")
time.sleep(3)

print("Calling adventure_wait()...")
try:
    state = conn.adventure_wait()
    print("yourTurn received in %.1fs!" % (time.time()-t0))
    print("State:", (state[:200] if state else "None"))
except Exception as e:
    print("adventure_wait FAILED:", e)

print("Done")
