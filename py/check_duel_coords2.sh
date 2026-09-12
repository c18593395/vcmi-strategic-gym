#!/bin/bash
set -e
PYBIN=/home/administrator/vcmi-workspace/venv/bin/python3
MAPS=/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps

$PYBIN - "$MAPS" <<'PY'
import sys, zipfile, json, os
maps_dir = sys.argv[1]
duel_files = [f for f in sorted(os.listdir(maps_dir)) if '_duel' in f]
for fname in duel_files:
    p = os.path.join(maps_dir, fname)
    with zipfile.ZipFile(p) as z:
        h = json.loads(z.read('header.json'))
        o = json.loads(z.read('objects.json'))
    print(f"\n=== {fname} ===")
    for key in ['hero_0','town_0','hero_1','town_1']:
        if key in o:
            obj = o[key]
            owner = obj.get('options',{}).get('owner','?')
            sub = obj.get('subtype','?')
            x = obj.get('x','?')
            y = obj.get('y','?')
            print(f"  {key}: owner={owner}, subtype={sub}, x={x}, y={y}")
    # 计算曼哈顿距离
    h0 = o.get('hero_0',{}); t0 = o.get('town_0',{})
    h1 = o.get('hero_1',{}); t1 = o.get('town_1',{})
    d0 = abs(h0.get('x',0)-t0.get('x',0)) + abs(h0.get('y',0)-t0.get('y',0))
    d1 = abs(h1.get('x',0)-t1.get('x',0)) + abs(h1.get('y',0)-t1.get('y',0))
    print(f"  red_hero→red_town dist={d0}, blue_hero→blue_town dist={d1}")
PY
