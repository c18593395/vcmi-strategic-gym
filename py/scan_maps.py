#!/usr/bin/env python3
"""
C4.1: 全地图扫描脚本 — 从 WSL VCMI data/Maps 枚举所有 .h3m 文件，
     每张图快速跑 3 步测试是否可进入 yourTurn 且无 crash，
     输出可用列表到 available_maps.json。

调用方式（在 WSL 中运行）：
    wsl -d Ubuntu -- bash -c '
        export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
        export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
        python3 /mnt/d/Bigdata/hero3_fresh/scan_maps.py
    '
"""
import os
import subprocess, json, os, tempfile, glob, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# === 配置 ===
VENV = os.environ.get("VENV", "/home/administrator/vcmi-workspace/venv/bin/python")
RUNNER = os.environ.get("RUNNER", "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py")
MAPS_DIR = os.environ.get("MAPS_DIR", "/home/administrator/vcmi-strategic/vcmi/data/Maps")
OUTPUT = os.environ.get("OUTPUT", "/mnt/d/Bigdata/hero3_fresh/available_maps.json")
STEPS = 3          # 快速测试只需 3 步
MAP_TIMEOUT = 30   # 每张图超时 30s
MAX_WORKERS = 8    # 并行 8 路（WSL 可承受）

# 共享环境变量（一次构造，所有 subprocess 复用）
BASE_ENV = os.environ.copy()
BASE_ENV["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
BASE_ENV["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

# 线程安全的锁（logging）
print_lock = threading.Lock()


def test_one_map(h3m_path: str):
    """测试单张图：运行 ep_runner_one.py，返回 (mapname, success, errmsg)"""
    mapname = os.path.basename(h3m_path)
    traj_path = None
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            traj_path = f.name

        proc = subprocess.Popen(
            [VENV, RUNNER, str(STEPS), traj_path, mapname],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=BASE_ENV,
        )
        proc.wait(timeout=MAP_TIMEOUT)

        with open(traj_path) as f:
            d = json.load(f)

        nz = d.get("steps", 0)
        has_error = d.get("error")

        if nz > 0 and not has_error:
            with print_lock:
                print(f"  ✅ {mapname}: {nz} steps")
            return (mapname, True, None)
        else:
            reason = has_error or f"steps={nz}"
            with print_lock:
                print(f"  ❌ {mapname}: {reason}")
            return (mapname, False, reason)

    except subprocess.TimeoutExpired:
        with print_lock:
            print(f"  ⏰ {mapname}: timeout ({MAP_TIMEOUT}s)")
        return (mapname, False, "timeout")
    except Exception as e:
        with print_lock:
            print(f"  💥 {mapname}: {e}")
        return (mapname, False, str(e))
    finally:
        if traj_path and os.path.exists(traj_path):
            try:
                os.unlink(traj_path)
            except OSError:
                pass


def main():
    # 1. 枚举所有 .h3m 文件
    h3m_files = sorted(glob.glob(os.path.join(MAPS_DIR, "*.h3m")))
    total = len(h3m_files)
    print(f"🔍 Found {total} .h3m maps in {MAPS_DIR}")

    if total == 0:
        print("⚠️  No maps found! Check MAPS_DIR path.")
        result = {"maps": [], "count": 0, "total": 0, "failed": []}
        with open(OUTPUT, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"📄 Written to {OUTPUT}")
        sys.exit(0)

    # 2. 并行扫描
    ok = []
    failed = []
    completed = 0

    print(f"🚀 Scanning {total} maps with {MAX_WORKERS} workers ({STEPS} steps each, {MAP_TIMEOUT}s timeout)...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        fut_to_map = {executor.submit(test_one_map, h3m): h3m for h3m in h3m_files}
        for fut in as_completed(fut_to_map):
            mapname, success, reason = fut.result()
            if success:
                ok.append(mapname)
            else:
                failed.append(mapname)
            completed += 1

            # 每 20 张图打印一次进度
            if completed % 20 == 0 or completed == total:
                with print_lock:
                    print(f"📊 Progress: {completed}/{total}  ok={len(ok)}  failed={len(failed)}")

    # 3. 输出结果
    result = {
        "maps": sorted(ok),
        "count": len(ok),
        "total": total,
        "failed": sorted(failed),
    }

    with open(OUTPUT, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"✅ Scan complete!")
    print(f"   Total maps:   {total}")
    print(f"   Available:    {len(ok)}")
    print(f"   Failed:       {len(failed)}")
    if failed:
        print(f"   Failed maps:  {', '.join(failed[:10])}{'...' if len(failed) > 10 else ''}")
    print(f"📄 Output:      {OUTPUT}")


if __name__ == "__main__":
    main()
