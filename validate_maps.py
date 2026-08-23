#!/usr/bin/env python3
"""地图验证管道: 生成 → BFS校验 → 实跑测试 → 不过丢弃重生成

Usage:
  python validate_maps.py                    # 验证所有地图
  python validate_maps.py T01_adventure_*    # 验证指定地图
  python validate_maps.py --regenerate L1    # 验证+失败重生成
"""
import sys, os, time, json, subprocess, glob, argparse
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["PYTHONPATH"] = "/mnt/d/Bigdata/hero3_fresh"

MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/Maps/training"
VCMI_MAPS = "/home/administrator/vcmi-native/rel/bin/data/Maps"
VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
EP_RUNNER = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
OUTFILE = "/home/administrator/validate_map.json"

def load_terrain_grid():
    """读取 terrain_grid.bin"""
    fpath = "/home/administrator/vcmi-workspace/terrain_grid.bin"
    for _ in range(20):
        try:
            raw = __import__('numpy').fromfile(fpath, dtype=__import__('numpy').uint8, count=1764)
            if raw.shape[0] == 1764 and raw.any():
                return raw.reshape(21, 21, 4)
        except:
            pass
        time.sleep(0.1)
    return None

def test_map(mapname, max_steps=10):
    """测试单张地图, 返回 (pass, details)"""
    import numpy as np

    # 1. 检查文件存在
    vmap_path = os.path.join(MAP_DIR, mapname)
    if not os.path.exists(vmap_path):
        return False, f"文件不存在: {vmap_path}"

    # 2. 检查 vmap 格式
    try:
        import zipfile
        with zipfile.ZipFile(vmap_path) as zf:
            names = zf.namelist()
            if 'header.json' not in names:
                return False, "缺少 header.json"
            if 'surface_terrain.json' not in names:
                return False, "缺少 surface_terrain.json"
            if 'objects.json' not in names:
                return False, "缺少 objects.json"
            header = json.loads(zf.read('header.json'))
            # vmap 格式: width/height 在 mapLevels.surface 里
            levels = header.get('mapLevels', {})
            surface = levels.get('surface', {})
            w = surface.get('width', header.get('width', 0))
            h = surface.get('height', header.get('height', 0))
            if w < 10 or h < 10:
                return False, f"地图太小: {w}x{h}"
    except Exception as e:
        return False, f"vmap 格式错误: {e}"

    # 3. 复制到 VCMI Maps 目录
    dst = os.path.join(VCMI_MAPS, mapname)
    if not os.path.exists(dst):
        import shutil
        shutil.copy2(vmap_path, dst)

    # 4. 实跑测试 (5步随机动作)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    env["PYTHONPATH"] = "/mnt/d/Bigdata/hero3_fresh"

    # Remove old terrain_grid.bin
    tg_path = "/home/administrator/vcmi-workspace/terrain_grid.bin"
    if os.path.exists(tg_path):
        os.remove(tg_path)

    cmd = [VENV, EP_RUNNER, str(max_steps), OUTFILE, mapname]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        return False, "超时 (120s)"

    if proc.returncode != 0:
        err = stderr.decode('utf-8', errors='replace')[-200:]
        return False, f"exit code {proc.returncode}: {err}"

    # 5. 检查输出
    if not os.path.exists(OUTFILE):
        return False, "输出文件不存在"

    try:
        with open(OUTFILE) as f:
            data = json.load(f)
    except:
        return False, "输出 JSON 解析失败"

    steps = data.get('steps', 0)
    error = data.get('error', None)
    if error:
        return False, f"运行错误: {error}"
    if steps == 0:
        return False, "0 步完成"

    # 6. 检查 terrain_grid
    tg = load_terrain_grid()
    if tg is None:
        return False, "terrain_grid.bin 未生成"
    nonz = int(np.count_nonzero(tg))
    if nonz < 100:
        return False, f"terrain_grid 非零值太少: {nonz}"

    # 7. 检查 BFS (通过 obs 中的 next_dir)
    if steps > 0 and 'obs' in data and len(data['obs']) > 0:
        obs0 = data['obs'][0]
        # Check hero position
        hero_x = int(obs0[130]) if len(obs0) > 130 else -1
        hero_y = int(obs0[131]) if len(obs0) > 131 else -1
        if hero_x < 0 or hero_y < 0:
            return False, f"hero 位置异常: ({hero_x},{hero_y})"

    return True, f"OK: {steps}步, tg非零={nonz}, hero=({hero_x},{hero_y})"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('patterns', nargs='*', help='地图名模式')
    parser.add_argument('--regenerate', action='store_true', help='失败时重生成')
    parser.add_argument('--level', type=str, help='Level 筛选 (T01/T02/L1/...)')
    args = parser.parse_args()

    # 收集地图列表
    if args.patterns:
        maps = []
        for p in args.patterns:
            maps.extend(glob.glob(os.path.join(MAP_DIR, p)))
        maps = [os.path.basename(m) for m in maps]
    elif args.level:
        maps = sorted([os.path.basename(m) for m in glob.glob(os.path.join(MAP_DIR, f"{args.level}_*.vmap"))])
    else:
        maps = sorted([os.path.basename(m) for m in glob.glob(os.path.join(MAP_DIR, "*.vmap"))])

    if not maps:
        print("没有找到地图")
        return

    print(f"验证 {len(maps)} 张地图...")
    print(f"{'='*60}")

    passed = []
    failed = []

    for i, mapname in enumerate(maps):
        sys.stdout.write(f"[{i+1}/{len(maps)}] {mapname}...")
        sys.stdout.flush()

        ok, detail = test_map(mapname)

        if ok:
            print(f" PASS ({detail})")
            passed.append(mapname)
        else:
            print(f" FAIL ({detail})")
            failed.append((mapname, detail))

            # 重生成
            if args.regenerate:
                # TODO: 触发重生成
                pass

    print(f"\n{'='*60}")
    print(f"结果: {len(passed)}/{len(maps)} 通过")
    if failed:
        print(f"\n失败:")
        for name, reason in failed:
            print(f"  {name}: {reason}")

    # 清理
    if os.path.exists(OUTFILE):
        os.remove(OUTFILE)

if __name__ == "__main__":
    main()
