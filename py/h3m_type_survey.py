#!/usr/bin/env python3
"""官方 H3M 地图全量类型分类统计 (2026-09-19)
口径复用 pick_flat_h3m.py + scripts/h3m_tool.py (parse_header/parse_objects/terrain 读法/flood 8邻连通)。
与 pick_flat 的区别: 不淘汰任何图, 纯分类统计。
  维度: 版本 / 层结构(单层|地下层|无门) / 岛屿(陆地分量) / 水域语义(strict|sealed|open)
       / 玩家数 / 队伍(同盟) / 尺寸 / 地形分布 / 玩法标志(胜利条件|水晶|事件|传送|怪物)
       / H3 风险(HOTA|UNDERGROUND|ZMAX|GATE|OPEN_WATER|TEAMS) / 可入池(单层无岛可转换子集)
产物: py/h3m_type_survey.json + 控制台分类汇总表
用法: python h3m_type_survey.py [maps_dir]
"""
import gzip
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from h3m_tool import AB, CHR, HOTA, ROE, SOD, WOG, parse_header, parse_objects  # noqa: E402

VER_NAME = {ROE: 'ROE', AB: 'AB', SOD: 'SOD', CHR: 'CHR', WOG: 'WOG', HOTA: 'HOTA'}

T_WATER, T_ROCK = 8, 9
WATER_OBJS = {'SHIPYARD', 'SEA_CHEST', 'SHIPWRECK', 'SHIPWRECK_SURVIVOR',
              'FLOTSAM', 'DERELICT_SHIP', 'OCEAN_BOTTLE'}
LAND_SET = set(range(10)) - {T_WATER, T_ROCK}  # 可穿陆地 (subterra 算陆, 有地下层走门)
NB8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

VICTORY = {-1: '标准', 0: '宝物', 1: '集兵', 2: '集资源', 3: '建城', 4: '水晶',
            5: '击杀英雄', 6: '占城', 7: '击破怪物', 8: '占居住', 9: '占矿',
            10: '送物', 11: '清怪(HOTA)', 12: '存活天数(HOTA)'}
LOSS = {-1: '标准', 0: '失城', 1: '失英雄', 2: '限时'}


def read_terrain(path, w, terrain_offset):
    with open(path, 'rb') as f:
        raw = gzip.decompress(f.read())
    return [[raw[terrain_offset + (y * w + x) * 7] for x in range(w)] for y in range(w)]


def flood(grid, w, want, blocked):
    comps = [0] * (w * w)
    seen = [[False] * w for _ in range(w)]
    n = 0
    for y in range(w):
        for x in range(w):
            if seen[y][x] or grid[y][x] not in want or grid[y][x] in blocked:
                continue
            n += 1
            seen[y][x] = True
            comps[y * w + x] = n
            stack = [(x, y)]
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


def dist1(v):
    """分布桶: ≤3 / 4-9 / 10-49 / ≥50"""
    if v <= 3:
        return f'≤3({v})'
    if v <= 9:
        return '4-9'
    if v <= 49:
        return '10-49'
    return '≥50'


def analyze(path, info):
    w, off = info['size'], info['terrain_offset']
    grid = read_terrain(path, w, off)
    n = w * w
    tdist = Counter()
    for y in range(w):
        for x in range(w):
            tdist[grid[y][x]] += 1

    water_ct = tdist[T_WATER]
    rock_ct = tdist[T_ROCK]

    # 水面连通 + 是否触达边缘水陆交界 (水可被船穿, 岩阻断)
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
                        elif grid[ny][nx] != T_WATER:
                            water_touched = True
                    if water_touched:
                        break
            if water_touched:
                break

    # 陆地连通 (非 water/rock; 跨层禁用 → 单层图无跨层格)
    land_comps, land_n = flood(grid, w, LAND_SET, {T_WATER, T_ROCK})
    land_dist = Counter(land_comps[y * w + x] for y in range(w) for x in range(w)
                        if land_comps[y * w + x])

    # 孤岛 = 陆地分量中不含任何玩家出生点/关键对象的 (主陆 = 含锚点分量, 无锚点时取最大分量)
    types = Counter()
    anchors = []
    obj = parse_objects(path)
    zmax = 0
    gates = 0
    water_objs = 0
    has_grail = has_event = has_wagon = has_monster = False
    for o in obj['objects']:
        t = o['type']
        types[t] += 1
        zmax = max(zmax, o['z'])
        if t == 'BORDER_GATE':
            gates += 1
        if t in WATER_OBJS:
            water_objs += 1
        if t == 'GRAIL':
            has_grail = True
        if t == 'EVENT':
            has_event = True
        if t == 'WAGON':
            has_wagon = True
        if t in ('RANDOM_MONSTER', 'RANDOM_MONSTER_L1', 'RANDOM_MONSTER_L2',
                  'RANDOM_MONSTER_L3', 'RANDOM_MONSTER_L4', 'RANDOM_MONSTER_L6',
                  'RANDOM_MONSTER_L7', 'CREATURE_GENERATOR1', 'CREATURE_GENERATOR2',
                  'CREATURE_GENERATOR3', 'CREATURE_GENERATOR4'):
            has_monster = True
        if t in ('HERO', 'RANDOM_HERO', 'TOWN', 'RANDOM_TOWN', 'MINE',
                 'BORDER_GATE', 'GARRISON', 'GARRISON2'):
            anchors.append((o['x'], o['y']))
    for p in info['players']:
        mt = p.get('main_town')
        if mt:
            anchors.append((mt[0], mt[1]))

    anchor_comps = set(land_comps[y * w + x] for (x, y) in anchors if land_comps[y * w + x])
    main_ids = anchor_comps or (
        {c for c in land_dist if land_dist[c] == max(land_dist.values())} if land_dist else set())
    island_ids = set(land_dist) - main_ids
    islands_ct = sum(land_dist[i] for i in island_ids)

    # 水域语义三态 (同 pick_flat: strict 无水 / sealed 岩中封闭水体 / open 需造船)
    in_land = [land_comps[y * w + x] for (x, y) in anchors if land_comps[y * w + x]]
    anchor_land = len(set(in_land))
    if water_ct == 0:
        cat = 'strict'
    elif not water_touched and land_n == 1 and anchor_land <= 1:
        cat = 'sealed'
    else:
        cat = 'open'

    ver = info['version']
    reject = [x for x in [
        'HOTA' if ver == HOTA else '',
        'UNDERGROUND' if info['has_underground'] else '',
        f'ZMAX={zmax}' if zmax else '',
        'GATE' if gates else '',
        'OPEN_WATER' if cat == 'open' else '',
        f'TEAMS={info["teams"]}' if info['teams'] != 0 else '',
    ] if x]
    poolable = not reject and cat in ('strict', 'sealed')

    return {
        'name': os.path.splitext(os.path.basename(path))[0],
        'h3m': os.path.basename(path),
        'version': VER_NAME.get(ver, str(ver)),
        'size': w,
        'players': len(info['players']),
        'teams': info['teams'],
        'difficulty': info['difficulty'],
        'victory': VICTORY.get(info['victory'], str(info['victory'])),
        'loss': LOSS.get(info['loss'], str(info['loss'])),
        'has_underground': info['has_underground'],
        'zmax': zmax,
        'border_gates': gates,
        'layer': '单层' if (info['has_underground'] == 0 and zmax == 0 and gates == 0)
                 else ('有门' if gates else '地下层'),
        'category': cat,
        'water': water_ct, 'water_pct': round(100.0 * water_ct / n, 1),
        'rock': rock_ct, 'rock_pct': round(100.0 * rock_ct / n, 1),
        'swamp': tdist.get(4, 0), 'swamp_pct': round(100.0 * tdist.get(4, 0) / n, 1),
        'terrain_dist': tdist,
        'land_components': land_n,
        'island_components': len(island_ids),
        'island_cells': islands_ct,
        'has_island': land_n > 1 and len(island_ids) > 0,
        'islands_dist': [dist1(land_dist[i]) for i in island_ids] if island_ids else [],
        'water_comps': water_n,
        'water_touched': water_touched,
        'water_objs': water_objs,
        'obj_count': obj['obj_count'],
        'obj_types': types,
        'grail': has_grail, 'event': has_event, 'wagon': has_wagon, 'monster': has_monster,
        'reject': ';'.join(reject),
        'poolable': poolable,
    }


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
            row = analyze(fp, info)
        except Exception as e:
            bad.append((fn, type(e).__name__ + ':' + str(e)[:80]))
            continue
        rows.append(row)

    total = len(rows)

    def dist(key, names=None, buckets=None):
        c = Counter()
        for r in rows:
            c[r[key]] += 1
        return c

    by_ver = dist('version')
    by_layer = dist('layer')
    by_cat = dist('category')
    by_ug = dist('has_underground')
    by_players = dist('players')
    by_teams = dist('teams')
    by_size = dist('size')
    by_land = dist('land_components')
    by_illand = dist('island_components')

    island_ct = sum(1 for r in rows if r['has_island'])
    grail_ct = sum(1 for r in rows if r['grail'])
    event_ct = sum(1 for r in rows if r['event'])
    wagon_ct = sum(1 for r in rows if r['wagon'])
    monster_ct = sum(1 for r in rows if r['monster'])
    poolable = [r for r in rows if r['poolable']]
    pool_names = sorted(r['name'] for r in poolable)

    def print_dist(title, c, order=None):
        print(f'\n── {title} ' + '─' * max(0, 40 - len(title) * 2))
        keys = order if order else sorted(c, key=lambda k: (-c[k], str(k)))
        for k in keys:
            if k not in c:
                continue
            bar = '#' * c[k]
            names = sorted(r['name'] for r in rows if r.get(order_key_for(title), k) if order_key_for(title))
            # 仅对玩家数/尺寸/版本/类别打印图名清单
            if title in ('玩家数', '尺寸', '版本', '水域语义', '层结构') :
                kk = {'玩家数': 'players', '尺寸': 'size', '版本': 'version',
                      '水域语义': 'category', '层结构': 'layer'}[title]
                names = sorted(r['name'] for r in rows if r[kk] == k)
                print(f'  {str(k):8s} {c[k]:3d}  {bar}')
                print(f'           {" ".join(names)}')
            else:
                print(f'  {str(k):8s} {c[k]:3d}  {bar}')

    def order_key_for(title):
        return None

    print(f'官方 H3M 全量分类统计  maps_dir={d}  总图={total}  解析失败={len(bad)}')
    if bad:
        print(f'解析失败: {bad}')

    print_dist('版本', by_ver)
    print_dist('层结构', by_layer, order=['单层', '有门', '地下层'])
    print_dist('水域语义', by_cat, order=['strict', 'sealed', 'open'])
    print(f'\n── 岛屿/陆地连通  有岛={island_ct} 张 · 陆地分量分布 {dict(by_land)} · 孤岛数分布 {dict(by_illand)}')
    print_dist('玩家数', by_players)
    print_dist('队伍', by_teams)
    print_dist('尺寸', by_size)

    # 交叉: 层结构 × 岛屿 × 水域
    cross = Counter((r['layer'], '有岛' if r['has_island'] else '无岛', r['category']) for r in rows)
    print('\n── 交叉矩阵 层结构 × 岛屿 × 水域语义 (count)')
    for k, v in sorted(cross.items()):
        print(f'  {k[0]} / {k[1]} / {k[2]:7s} : {v}')

    # 玩法标志
    print('\n── 玩法标志  水晶=%d  事件=%d  传送=%d  随机怪物生成=%d' %
          (grail_ct, event_ct, wagon_ct, monster_ct))
    print_dist('胜利条件', dist('victory'))
    print_dist('失败条件', dist('loss'))

    print('\n── 风险标签 (H3 转换死因维度, 一张图可命中多个)')
    for tag in ('HOTA', 'UNDERGROUND', 'GATE', 'OPEN_WATER'):
        ct = sum(1 for r in rows if tag in r['reject'].split(';'))
        print(f'  {tag:12s} {ct}')
    zmax_ct = sum(1 for r in rows if any(t.startswith('ZMAX=') for t in r['reject'].split(';') if t))
    teams_ct = sum(1 for r in rows if r['teams'] != 0)
    print(f'  ZMAX(地下对象) {zmax_ct}')
    print(f'  TEAMS(同盟)    {teams_ct}')

    print(f'\n── 可入池 (无风险标签 且 水域∈strict/sealed): {len(poolable)} 张')
    print('   ' + ' '.join(pool_names))

    slim = [{k: (dict(v) if k in ('terrain_dist', 'obj_types') else v)
             for k, v in r.items() if k not in ('terrain_dist', 'obj_types')}
            | {'terrain_dist': {str(k2): v2 for k2, v2 in r['terrain_dist'].items()},
               'obj_types': {k2: v2 for k2, v2 in sorted(r['obj_types'].items(), key=lambda t: -t[1])}}
            for r in rows]
    out_json = os.path.join(root, 'py', 'h3m_type_survey.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({
            'maps_dir': d,
            'total': total,
            'parse_fail': bad,
            'counts': {
                'by_version': dict(by_ver), 'by_layer': dict(by_layer),
                'by_category': dict(by_cat), 'by_underground': dict(by_ug),
                'by_players': dict(by_players), 'by_teams': dict(by_teams),
                'by_size': dict(by_size), 'by_land_components': dict(by_land),
                'by_island_components': dict(by_illand),
                'island_maps': island_ct, 'grail': grail_ct, 'event': event_ct,
                'wagon': wagon_ct, 'monster': monster_ct,
            },
            'cross': {f'{a}|{b}|{c}': v for (a, b, c), v in cross.items()},
            'poolable': pool_names,
            'rows': slim,
        }, f, ensure_ascii=False, indent=1)
    print(f'\nJSON: {out_json}')


if __name__ == '__main__':
    main()
