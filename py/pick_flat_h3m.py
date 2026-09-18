#!/usr/bin/env python3
"""H3M 官方图选图: 单层 / 无地下 / 不需要过河 (不需要造船)
P10 选图用.

判定口径 (与"要过河"等价的形式化):
  硬条件 (硬条件任一不满足 → 淘汰):
    H1 has_underground == 0        只有一层, 无地下层
    H2 全对象 z == 0               无地下对象 (H1 的独立证据链)
    H3 无 BORDER_GATE              无地下出入口
    H4 version != HOTA             HOTA 格式 h3mtxt/h3m2vmap 拒读 (P10 C 步边界)
  渡河条件 (决定"需不需要过水面"):
    W1 全图 water(8) 格数 == 0                          → strict (完全无水)
    W2 或: water>0 但水面 8 邻不连任何边缘水陆交界格,
         且全图陆地 (非 water/rock, 8 邻, 跨层禁用) 恰 1 个连通分量,
         且所有关键点 (玩家出生点/英雄/城镇/矿/随机英雄/边境门) 都在该分量内
                                                        → sealed (水面为岩中孤立封闭水体,
                                                          英雄物理上够不到 → 不需要造船)
    否则 → open (需造船, 淘汰)
  附加统计 (不淘汰, 供选图排序):
    水生物体数 (SHIPYARD/SEA_CHEST/SHIPWRECK/SHIPWRECK_SURVIVOR/FLOTSAM/DERELICT_SHIP/OCEAN_BOTTLE)
    玩家数 / 队伍数 (teams: 0=单组对抗=正常对抗图, >=1=两队及以上同盟图, 排除 teams>=1)

产物: py/h3m_flat_pool.csv + py/h3m_flat_pool.json
用法: python pick_flat_h3m.py [maps_dir]
"""
import csv
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from h3m_tool import AB, CHR, HOTA, ROE, SOD, WOG, parse_header, parse_objects  # noqa: E402

VER_NAME = {ROE: 'ROE', AB: 'AB', SOD: 'SOD', CHR: 'CHR', WOG: 'WOG', HOTA: 'HOTA'}

T_WATER, T_ROCK, T_GRASS = 8, 9, 2

# 水生物体 (出现即代表图有水域语义)
WATER_OBJS = {'SHIPYARD', 'SEA_CHEST', 'SHIPWRECK', 'SHIPWRECK_SURVIVOR',
              'FLOTSAM', 'DERELICT_SHIP', 'OCEAN_BOTTLE'}
# 关键点类型 (必须落在同一陆地连通分量内)
KEY_OBJS = {'HERO', 'RANDOM_HERO', 'TOWN', 'RANDOM_TOWN', 'MINE', 'BORDER_GATE',
            'GARRISON', 'GARRISON2'}

NB8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def read_terrain(path, w, has_ug, terrain_offset):
    """表层 terrain 网格 (w x w); has_ug 时跳过地下层"""
    with open(path, 'rb') as f:
        raw = gzip.decompress(f.read())
    grid = []
    for y in range(w):
        row = [raw[terrain_offset + (y * w + x) * 7] for x in range(w)]
        grid.append(row)
    return grid


def flood(grid, w, want, blocked):
    """8 邻连通分量标号: want=参与地形集合, blocked=不可穿越地形集合.
    返回 (comps, n): comps[y*w+x] = 分量号 (0 = 非参与格), n = 分量数"""
    comps = [0] * (w * w)
    seen = [[False] * w for _ in range(w)]
    n = 0
    for y in range(w):
        for x in range(w):
            if seen[y][x] or grid[y][x] not in want or grid[y][x] in blocked:
                continue
            n += 1
            seen[y][x] = True
            stack = [(x, y)]
            comps[y * w + x] = n
            while stack:
                cx, cy = stack.pop()
                for dx, dy in NB8:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < w and not seen[ny][nx]:
                        nt = grid[ny][nx]
                        if nt in want and nt not in blocked:
                            seen[ny][nx] = True
                            comps[ny * w + nx] = n
                            stack.append((nx, ny))
    return comps, n


def analyze(path, info):
    w, off = info['size'], info['terrain_offset']
    grid = read_terrain(path, w, info['has_underground'], off)

    water_ct = sum(1 for y in range(w) for x in range(w) if grid[y][x] == T_WATER)
    rock_ct = sum(1 for y in range(w) for x in range(w) if grid[y][x] == T_ROCK)
    nongrass = sum(1 for y in range(w) for x in range(w) if grid[y][x] != T_GRASS)

    # 水面连通 + 是否触达边缘水陆交界格
    water_comps, water_n = flood(grid, w, {T_WATER}, set())
    water_touched = False
    if water_n:
        for y in range(w):
            for x in range(w):
                if grid[y][x] == T_WATER:
                    for dx, dy in NB8:
                        nx, ny = x + dx, y + dy
                        if nx < 0 or ny < 0 or nx >= w or ny >= w:
                            water_touched = True
                        elif grid[ny][nx] != T_WATER:  # 水陆交界
                            water_touched = True
                    if water_touched:
                        break
            if water_touched:
                break

    # 陆地连通 (非 water/rock, 跨层禁用 → 单层图无跨层格)
    land_ct = 0
    for y in range(w):
        for x in range(w):
            t = grid[y][x]
            if t != T_WATER and t != T_ROCK:
                land_ct += 1
    land_comps, land_n = flood(grid, w, set(range(10)) - {T_WATER, T_ROCK}, {T_WATER, T_ROCK})
    return grid, water_ct, rock_ct, nongrass, water_comps, water_n, water_touched, \
        land_comps, land_n, land_ct


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, 'vcmi', 'data', 'Maps')
    rows, bad = [], []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.h3m'):
            continue
        fp = os.path.join(d, fn)
        try:
            info = parse_header(fp)
        except Exception as e:
            bad.append((fn, 'header:' + type(e).__name__))
            continue

        ver, w = info['version'], info['size']
        has_ug, teams = info['has_underground'], info['teams']
        try:
            obj = parse_objects(fp)
        except Exception as e:
            bad.append((fn, 'objects:' + type(e).__name__))
            continue

        grid, water_ct, rock_ct, nongrass, water_comps, water_n, water_touched, \
            land_comps, land_n, land_ct = analyze(fp, info)

        types, water_objs, gates, zmax = {}, [], [], 0
        keys = []
        for o in obj['objects']:
            t = o['type']
            types[t] = types.get(t, 0) + 1
            if t in WATER_OBJS:
                water_objs.append(t)
            if t == 'BORDER_GATE':
                gates.append(1)
            zmax = max(zmax, o['z'])
            if t in KEY_OBJS:
                keys.append((o['x'], o['y']))

        # 玩家出生点 (main_town 是 (x,y,z) 三元组; 取 x,y)
        anchor = list(keys)  # 关键点
        for p in info['players']:
            mt = p.get('main_town')
            if mt:
                anchor.append((mt[0], mt[1]))
        in_land = [land_comps[y * w + x] for (x, y) in anchor if land_comps[y * w + x]]
        anchor_land = len(set(in_land))

        hard_ok = (ver != HOTA and has_ug == 0 and zmax == 0 and not gates)

        if water_ct == 0:
            cat = 'strict'
        elif not water_touched and land_n == 1 and len(set(in_land)) <= 1:
            cat = 'sealed'
        else:
            cat = 'open'
        rec_pass = int(hard_ok and cat in ('strict', 'sealed') and teams == 0)

        rec = {
            'pass': rec_pass,
            'name': os.path.splitext(fn)[0],
            'size': w,
            'players': len(info['players']),
            'teams': teams,
            'version': VER_NAME.get(ver, str(ver)),
            'difficulty': info['difficulty'],
            'category': cat,
            'water': water_ct,
            'rock': rock_ct,
            'nongrass': nongrass,
            'water_touched': water_touched,
            'land_components': land_n,
            'obj_count': obj['obj_count'],
            'water_objs': len(water_objs),
            'hero': types.get('HERO', 0),
            'rhero': types.get('RANDOM_HERO', 0),
            'town': types.get('TOWN', 0),
            'rtown': types.get('RANDOM_TOWN', 0),
            'mine': types.get('MINE', 0),
            'garrison': types.get('GARRISON', 0) + types.get('GARRISON2', 0),
            'underground': has_ug,
            'zmax': zmax,
            'border_gates': len(gates),
            'victory': info['victory'],
            'loss': info['loss'],
            'skipped': obj['skipped_bytes'],
            'reject': '' if rec_pass else ';'.join([x for x in [
                'HOTA' if ver == HOTA else '',
                'UNDERGROUND' if has_ug else '',
                f'ZMAX={zmax}' if zmax else '',
                'GATE' if gates else '',
                'OPEN_WATER' if cat == 'open' else '',
                f'TEAMS={teams}' if teams != 0 else '',
            ] if x]),
            'h3m': fn,
        }
        rows.append(rec)

    ok = sorted([r for r in rows if r['pass']], key=lambda r: (r['size'], r['players'], r['name']))
    keys_csv = ['pass', 'category', 'name', 'size', 'players', 'version', 'difficulty',
                 'water', 'rock', 'nongrass', 'water_touched', 'land_components',
                 'obj_count', 'hero', 'rhero', 'town', 'rtown', 'mine', 'garrison',
                 'water_objs', 'teams', 'underground', 'zmax', 'border_gates',
                 'victory', 'loss', 'skipped', 'reject', 'h3m']
    out_csv = os.path.join(root, 'py', 'h3m_flat_pool.csv')
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=keys_csv, extrasaction='ignore')
        wr.writeheader()
        wr.writerows(sorted(rows, key=lambda r: (-r['pass'], r['size'], r['name'])))
    out_json = os.path.join(root, 'py', 'h3m_flat_pool.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'maps_dir': d, 'total': len(rows), 'parse_fail': bad,
                   'flat_pool': [r['h3m'] for r in ok],
                   'strict': [r['h3m'] for r in ok if r['category'] == 'strict'],
                   'sealed': [r['h3m'] for r in ok if r['category'] == 'sealed'],
                   'rows': rows}, f, ensure_ascii=False, indent=1)

    print(f'总图 {len(rows)}, 解析失败 {len(bad)}, 合格 {len(ok)} '
          f'(strict={sum(1 for r in ok if r["category"] == "strict")}, '
          f'sealed={sum(1 for r in ok if r["category"] == "sealed")})')
    if bad:
        print(f'解析失败: {bad}')
    hdr = f'{"类别":7s} {"图名":52s} {"尺寸":>6s} {"玩家":>4s} {"难度":>4s} {"对象":>5s} {"水":>6s} {"非草":>6s}'
    print(hdr)
    for r in ok:
        print(f'{r["category"]:7s} {r["name"]:52s} {r["size"]:4d}x{r["size"]:<1d} '
              f'{r["players"]:4d} {r["difficulty"]:4d} {r["obj_count"]:5d} '
              f'{r["water"]:6d} {r["nongrass"]:6d}')
    print(f'CSV : {out_csv}')
    print(f'JSON: {out_json}')


if __name__ == '__main__':
    main()
