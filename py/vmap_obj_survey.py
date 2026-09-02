#!/usr/bin/env python3
"""扫描 vmap 的 objects.json 对象类型集合 (vmap2h3m 范围调研用)"""
import json, sys, zipfile

for path in sys.argv[1:]:
    with zipfile.ZipFile(path) as z:
        objs = json.loads(z.read('objects.json'))
        hdr = json.loads(z.read('header.json'))
    if isinstance(objs, dict):
        objs = list(objs.values())
    types = {}
    for o in objs:
        if not isinstance(o, dict):
            continue
        t = o.get('type', '?')
        types.setdefault(t, set()).add(o.get('subtype', ''))
    print(f"== {path}")
    print(f"   header: name={hdr.get('name')!r} size={hdr.get('mapLevels')} players={list(hdr.get('players', {}).keys())}")
    for t in sorted(types):
        subs = sorted(types[t])
        print(f"   {t}: n=? subtypes={subs[:6]}{'...' if len(subs) > 6 else ''}")
