#!/usr/bin/env python3
"""
扫描 110 张可用 H3M 地图的起始位置 passability。
每张图跑 1 步，读 obs[-8:] 看有几格可通行。
输出按可通行数降序排列。
"""
import os
import subprocess, json, tempfile, os, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

VENV = os.environ.get("VENV", "/home/administrator/vcmi-workspace/venv/bin/python")
RUNNER = os.environ.get("RUNNER", "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py")
MAPS_JSON = os.environ.get("MAPS_JSON", "/mnt/d/Bigdata/hero3_fresh/available_maps.json")
OUTPUT = os.environ.get("OUTPUT", "/mnt/d/Bigdata/hero3_fresh/passability_ranking.json")
STEPS = 1
TIMEOUT = 30
MAX_WORKERS = 8

BASE_ENV = os.environ.copy()
BASE_ENV["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
BASE_ENV["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

lock = threading.Lock()

def check_one(mapname):
    traj_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            traj_path = f.name
        proc = subprocess.Popen(
            [VENV, RUNNER, str(STEPS), traj_path, mapname],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=BASE_ENV,
        )
        proc.wait(timeout=TIMEOUT)
        with open(traj_path) as f:
            d = json.load(f)
        if d.get("steps", 0) > 0 and d.get("obs") and len(d["obs"]) > 0:
            obs0 = d["obs"][0]
            passable = [int(v) for v in obs0[-8:]]
            n = sum(passable)
            with lock:
                print(f"  {n}/8  {mapname}")
            return (mapname, n, passable, None)
        else:
            return (mapname, -1, None, d.get("error") or f"steps={d.get('steps')}")
    except subprocess.TimeoutExpired:
        return (mapname, -1, None, "timeout")
    except Exception as e:
        return (mapname, -1, None, str(e))
    finally:
        if traj_path and os.path.exists(traj_path):
            try: os.unlink(traj_path)
            except: pass

def main():
    with open(MAPS_JSON) as f:
        data = json.load(f)
    maps = data.get("maps", [])
    total = len(maps)
    print(f"🔍 Checking starting passability for {total} maps...\n")

    results = []
    completed = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(check_one, m): m for m in maps}
        for fut in as_completed(fut_map):
            mapname, n, passable, err = fut.result()
            results.append((mapname, n, passable, err))
            completed += 1
            if completed % 10 == 0:
                print(f"  [{completed}/{total}]")

    # Sort: best first
    results.sort(key=lambda x: -x[1])

    print(f"\n{'='*60}")
    print(f"TOP 20 (best starting passability):")
    print(f"{'passable':>8}  {'map':<50}")
    print(f"{'-'*8}  {'-'*50}")
    for r in results[:20]:
        n = r[1]
        if n >= 0:
            bar = "#" * n + "." * (8 - n)
            print(f"  {bar}  {n}/8  {r[0]}")

    print(f"\nBOTTOM 10 (worst):")
    bottom = [r for r in results if r[1] >= 0][-10:]
    for r in reversed(bottom):
        n = r[1]
        bar = "#" * n + "." * (8 - n)
        print(f"  {bar}  {n}/8  {r[0]}")

    # Optional: print specific maps that are good for training
    print(f"\n📊 Summary:")
    counts = {}
    for r in results:
        n = r[1]
        if n >= 0:
            counts[n] = counts.get(n, 0) + 1
    for n in sorted(counts.keys()):
        print(f"  {n}/8 passable: {counts[n]} maps")

    good = [r for r in results if r[1] >= 4]
    print(f"\n✅ Maps with 4+ starting passable directions: {len(good)}")
    for r in good:
        print(f"  {r[0]}")

    # Save full results
    output_data = {
        "total_checked": len(results),
        "results": [{"map": r[0], "passable_count": r[1], "passable": r[2], "error": r[3]} for r in results],
    }
    with open(OUTPUT, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Full ranking: {OUTPUT}")

if __name__ == "__main__":
    main()
