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
    print(f"\n=== {fname} ===")
    with zipfile.ZipFile(p) as z:
        h = json.loads(z.read('header.json'))
        o_raw = z.read('objects.json')
    o = json.loads(o_raw)
    print(f"  mapLevels: {json.dumps(h.get('mapLevels',{}))}")
    print(f"  battleOnly: {h.get('battleOnly')}")
    print(f"  objects type: {type(o).__name__}, len: {len(o) if isinstance(o,(list,dict)) else '?'}")
    # objects 可能是 dict 或 list
    if isinstance(o, dict):
        # 打印所有 key
        for k,v in o.items():
            if 'town' in k.lower() or 'hero' in k.lower() or '1' in k or '2' in k:
                print(f"    key={k}: {json.dumps(v)[:200]}")
    elif isinstance(o, list):
        for obj in o:
            t = obj.get('type','') if isinstance(obj,dict) else str(obj)
            if 'town' in str(t).lower() or 'hero' in str(t).lower():
                print(f"    obj: {json.dumps(obj)[:200]}")
PY
