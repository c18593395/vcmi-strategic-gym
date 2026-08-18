#!/usr/bin/env python3
"""快速实测候选 2 人图出生点 passability (1 步, 读 obs[-8:])"""
import subprocess, json, tempfile, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
CANDIDATES = [
    "A Warm and Familiar Place.h3m",
    "Gorlam's Tentacle Swampland.h3m",
    "Twins.h3m",
    "Unexpected Inheritance.h3m",
    "Unholy Quest.h3m",
    "When Dragons Clash.h3m",
    "All for One.h3m",
    "Dungeon Keeper.h3m",  # 对照组: 已知被围
]
TIMEOUT = 60
MAX_WORKERS = 4

BASE_ENV = os.environ.copy()
BASE_ENV["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
BASE_ENV["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
BASE_ENV.pop("DISPLAY", None)

lock = threading = __import__("threading")

def check_one(mapname):
    traj_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            traj_path = f.name
        proc = subprocess.Popen(
            [VENV, RUNNER, "1", traj_path, mapname],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=BASE_ENV,
        )
        proc.wait(timeout=TIMEOUT)
        with open(traj_path) as f:
            d = json.load(f)
        if d.get("steps", 0) > 0 and d.get("obs") and len(d["obs"]) > 0:
            obs0 = d["obs"][0]
            # 3464 维: passable 在 [3211:3219] (v3 schema 固定偏移)
            passable = [int(v) for v in obs0[3211:3219]]
            n = sum(passable)
            # 额外读英雄位置
            extra = ""
            if len(obs0) > 3300:
                ah = int(obs0[3203])
                base = 128 + ah * 26
                if base + 4 < len(obs0):
                    extra = f" hero=({int(obs0[base+2])},{int(obs0[base+3])})"
            return (mapname, n, passable, extra, None)
        return (mapname, -1, None, "", d.get("error") or f"steps={d.get('steps')}")
    except subprocess.TimeoutExpired:
        return (mapname, -1, None, "", "timeout")
    except Exception as e:
        return (mapname, -1, None, "", str(e))
    finally:
        if traj_path and os.path.exists(traj_path):
            try: os.unlink(traj_path)
            except: pass

def main():
    print(f"Checking {len(CANDIDATES)} maps...")
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(check_one, m): m for m in CANDIDATES}
        for fut in as_completed(fut_map):
            mapname, n, passable, extra, err = fut.result()
            results.append((mapname, n, passable, extra, err))
            if err:
                print(f"  FAIL {mapname}: {err}")
            else:
                print(f"  {n}/8  {mapname}{extra}  passable={passable}")
    results.sort(key=lambda x: -x[1])
    print("\n=== SORTED ===")
    for r in results:
        n = r[1]
        if n >= 0:
            print(f"  {n}/8  {r[0]}{r[3]}")

if __name__ == "__main__":
    main()
