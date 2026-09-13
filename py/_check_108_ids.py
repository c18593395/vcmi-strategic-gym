import zipfile, json

for f in ['T06_adventure_72X72_02', 'T06_adventure_108X108_02_duel', 'T06_adventure_108X108_02']:
    p = f'/mnt/d/Bigdata/hero3_fresh/maps/training/{f}.vmap'
    with zipfile.ZipFile(p) as zf:
        raw = zf.read('objects.json')
        d = json.loads(raw)
        # 汇总所有 hero 和 town 的 type/subtype
        hero_types = set()
        town_types = set()
        hero_n = 0
        town_n = 0
        for k, v in d.items():
            if not isinstance(v, dict):
                continue
            t = v.get('type', '')
            st = v.get('subtype', '')
            if t == 'hero':
                hero_n += 1
                hero_types.add(f'{st}' if st else f'{t}')
            elif t == 'town' or 'town' in t:
                town_n += 1
                town_types.add(f'{st}' if st else f'{t}')
        # blue hero 数量
        raw2 = zf.read('header.json')
        h = json.loads(raw2)
        players = h.get('players', {})
        blue_heroes = players.get('blue', {}).get('heroes', {})
        red_heroes = players.get('red', {}).get('heroes', {})
        print(f'{f}: heroes={hero_n} towns={town_n} blue_heroes={len(blue_heroes)} red_heroes={len(red_heroes)} hero_subtypes={sorted(hero_types)} town_subtypes={sorted(town_types)}')
