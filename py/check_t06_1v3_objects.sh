#!/bin/bash
# T06 非 duel 图 (1v3) objects 蓝英雄数确认 (只读, 09-11)
cd /mnt/d/Bigdata/hero3_fresh
python3 << 'PYEOF'
import zipfile, json
for name in ['T06_adventure_72X72_01', 'T06_adventure_72X72_02']:
    p = f'maps/training/{name}.vmap'
    with zipfile.ZipFile(p) as z:
        objs = json.loads(z.read('objects.json'))
    blue = [(k, v) for k, v in objs.items() if k.startswith('hero') and isinstance(v, dict) and v.get('owner') == 'blue']
    red = [(k, v) for k, v in objs.items() if k.startswith('hero') and isinstance(v, dict) and v.get('owner') == 'red']
    guards = [k for k in objs if k.startswith('monster')]
    towns = [(k, v.get('owner','?')) for k, v in objs.items() if k.startswith('town')]
    print(f'=== {name} ===')
    print(f'  red heroes: {len(red)} {[(k, v.get("x"), v.get("y"), v.get("peasants")) for k,v in red]}')
    print(f'  blue heroes: {len(blue)} {[(k, v.get("x"), v.get("y"), v.get("peasants")) for k,v in blue]}')
    print(f'  guards: {len(guards)}')
    print(f'  towns: {towns}')
PYEOF
