#!/usr/bin/env python3
"""Phase A: Adventure API end-to-end validation."""

import sys, os, time, ctypes, argparse

# 09-23 路径环境化: 可用 VCMI_WORKSPACE_DIR 覆盖 (默认 ~/vcmi-workspace)
WORKSPACE = os.environ.get("VCMI_WORKSPACE_DIR") or os.path.expanduser("~/vcmi-workspace")
VCMI_REL = os.path.join(WORKSPACE, "vcmi", "rel", "bin")
CONN_REL = os.path.join(WORKSPACE, "vcmi_gym", "connectors", "rel")
VCMI_GYM = os.path.join(WORKSPACE, "vcmi_gym")

os.environ.setdefault("LD_LIBRARY_PATH", f"{VCMI_REL}:{CONN_REL}")
sys.path.insert(0, VCMI_GYM)

MAX_HEROES, MAX_TOWNS, MAX_PLAYERS = 8, 8, 8

class StrategicPlayer(ctypes.Structure):
    _fields_ = [("color", ctypes.c_int32), ("human", ctypes.c_int32),
                ("gold", ctypes.c_int32), ("wood", ctypes.c_int32),
                ("mercury", ctypes.c_int32), ("ore", ctypes.c_int32),
                ("sulfur", ctypes.c_int32), ("crystal", ctypes.c_int32),
                ("gems", ctypes.c_int32),
                ("hero_count", ctypes.c_int32), ("town_count", ctypes.c_int32),
                ("alive", ctypes.c_int32)]

class StrategicHero(ctypes.Structure):
    _fields_ = [("id", ctypes.c_int32), ("owner", ctypes.c_int32),
                ("pos_x", ctypes.c_int32), ("pos_y", ctypes.c_int32),
                ("pos_z", ctypes.c_int32),
                ("movement", ctypes.c_int32), ("max_movement", ctypes.c_int32),
                ("level", ctypes.c_int32),
                ("attack", ctypes.c_int32), ("defense", ctypes.c_int32),
                ("power", ctypes.c_int32), ("knowledge", ctypes.c_int32),
                ("mana", ctypes.c_int32), ("max_mana", ctypes.c_int32),
                ("exp", ctypes.c_int32),
                ("army_count", ctypes.c_int32 * 7),
                ("army_type", ctypes.c_int32 * 7),
                ("in_battle", ctypes.c_int32), ("name", ctypes.c_char * 32)]

class StrategicTown(ctypes.Structure):
    _fields_ = [("id", ctypes.c_int32), ("owner", ctypes.c_int32),
                ("pos_x", ctypes.c_int32), ("pos_y", ctypes.c_int32),
                ("pos_z", ctypes.c_int32), ("buildings", ctypes.c_int32),
                ("garrison", ctypes.c_int32 * 7),
                ("gold_income", ctypes.c_int32), ("name", ctypes.c_char * 32)]

class StrategicState(ctypes.Structure):
    _fields_ = [("day", ctypes.c_int32), ("week", ctypes.c_int32),
                ("month", ctypes.c_int32), ("current_player", ctypes.c_int32),
                ("map_width", ctypes.c_int32), ("map_height", ctypes.c_int32),
                ("has_underground", ctypes.c_int32), ("player_count", ctypes.c_int32),
                ("players", StrategicPlayer * MAX_PLAYERS),
                ("heroes", StrategicHero * MAX_HEROES),
                ("towns", StrategicTown * MAX_TOWNS),
                ("game_over", ctypes.c_int32), ("_version", ctypes.c_int32)]

def log_state(state):
    if not state: return
    print(f"  Day {state.day}.{state.week}.{state.month}"
          f" | Players: {state.player_count}"
          f" | Current: P{state.current_player}"
          f" | Map: {state.map_width}x{state.map_height}x{1 + state.has_underground}"
          f" | GameOver: {state.game_over}")
    for pi in range(state.player_count):
        p = state.players[pi]
        print(f"    P{pi}: gold={p.gold} heroes={p.hero_count} "
              f"towns={p.town_count} alive={p.alive}")
    for hi in range(MAX_HEROES):
        h = state.heroes[hi]
        if h.id >= 0:
            print(f"    Hero[{hi}]: id={h.id} owner=P{h.owner} "
                  f"pos=({h.pos_x},{h.pos_y},{h.pos_z}) "
                  f"lvl={h.level} mv={h.movement}/{h.max_movement} "
                  f"name={h.name.decode('utf-8', 'replace')}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="adventure-island-fire")
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--loglevel", default="info",
                        choices=["trace","debug","info","warn","error"])
    args = parser.parse_args()
    assert any(kw in args.map.lower() for kw in ["s1","mini","adventure"])

    print(f"Adventure API: map={args.map} steps={args.steps}")

    gss = None
    try:
        libml = ctypes.CDLL(f"{VCMI_REL}/libmlclient.so", use_errno=True)
        gss = ctypes.c_void_p.in_dll(libml, "g_strategic_state")
        print(f"  [*] g_strategic_state @ {gss}")
    except Exception as e:
        print(f"  [-] (non-fatal) {e}")

    from connectors.rel import connector_v13

    conn = connector_v13.ThreadConnector(
        maxlogs=100, bootTimeout=args.timeout,
        vcmiTimeout=args.timeout, userTimeout=args.timeout,
        red="MMAI_USER", redModel="",
        blue="StupidAI", blueModel="",
        mapname=args.map, seed=42,
        randomHeroes=0, randomObstacles=0, townChance=0,
        warmachineChance=0, randomArmies=False,
        randomArmyValueMin=500, randomArmyValueMax=1000,
        randomArmyTargetVar=0, tightFormationChance=0,
        randomTerrainChance=0, leftVipChance=0, rightVipChance=0,
        battlefieldPattern="", manaMin=0, manaMax=0,
        randomPrimarySkills=0, swapSides=0,
        loglevelGlobal=args.loglevel, loglevelAI=args.loglevel,
        loglevelNetwork="error", loglevelStats=args.loglevel,
        redAllowMlBot=False, blueAllowMlBot=False,
        statsMode="disabled", statsStorage="-", statsPersistFreq=100)
    print("  [*] ThreadConnector created")

    print("  [*] start()...")
    sys.stdout.flush()
    conn.start()
    print("  [*] VCMI started in adventure mode")
    time.sleep(2)

    print(f"\n  [*] Running {args.steps} cycles...")
    sys.stdout.flush()
    success = 0
    step = 0

    for step in range(1, args.steps + 1):
        t0 = time.time()
        try:
            code, ps = conn.adventure_wait()
            if code != 0:
                print(f"  [!] Step {step}: adventure_wait code={code}")
                break
            player = int(ps) if ps else -1
            print(f"  [OK] Step {step}: player={player} ({time.time()-t0:.1f}s)")

            if gss is not None:
                try:
                    vp = ctypes.cast(gss, ctypes.POINTER(ctypes.c_void_p))[0]
                    if vp:
                        log_state(StrategicState.from_address(vp))
                except Exception as e:
                    print(f"    state err: {e}")

            t1 = time.time()
            c2, m2 = conn.adventure_act(0)
            print(f"    [OK] act(0) -> {m2} ({time.time()-t1:.2f}s)")
            success += 1

            if gss is not None:
                try:
                    vp = ctypes.cast(gss, ctypes.POINTER(ctypes.c_void_p))[0]
                    if vp and StrategicState.from_address(vp).game_over != 0:
                        print(f"  [*] Game over")
                        break
                except: pass
        except Exception as e:
            print(f"  [!] Step {step}: {e}")
            try:
                for l in conn.getLogs()[-3:]:
                    print(f"    LOG: {l}")
            except: pass
            break
        print()

    print("  [*] shutdown()...")
    sys.stdout.flush()
    try:
        conn.shutdown()
        print("  [*] shutdown complete")
    except: print("  [-] shutdown exception (expected)")

    print(f"\n{'=' * 50}")
    if success >= args.steps:
        print(f"  ** PHASE A PASSED ** ({success}/{args.steps})")
        sys.exit(0)
    elif success > 0:
        print(f"  ** PHASE A PARTIAL ** ({success}/{args.steps})")
        sys.exit(1)
    else:
        print("  ** PHASE A FAILED **")
        sys.exit(1)

if __name__ == "__main__":
    main()
