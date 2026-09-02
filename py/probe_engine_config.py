#!/usr/bin/env python3
"""调研 VCMI core config 结构: creature/hero index 来源 (vmap2h3m 数据源)"""
import glob, json

root = '/home/administrator/vcmi-native/rel/bin'
cands = [
    root + '/Mods/vcmi/Content/config/creatures/*.json',
    root + '/config/creatures/*.json',
    root + '/Mods/vcmi/Content/config/heroes/*.json',
    root + '/config/heroes/*.json',
]
files = sorted(glob.glob(root + '/Mods/vcmi/Content/config/creatures/*.json')) or \
        sorted(glob.glob(root + '/config/creatures/*.json'))
print("creature files:", [f.split('/')[-1] for f in files][:8])
if files:
    d = json.load(open(files[0]))
    ks = list(d.keys())[:3]
    print("first entries:", ks)
    for k in ks:
        e = d[k]
        print(k, '->', json.dumps({f: e.get(f) for f in ('index', 'shortIdentifier', 'faction', 'level', 'name') if f in e}, ensure_ascii=False)[:300])

hfiles = sorted(glob.glob(root + '/Mods/vcmi/Content/config/heroes/*.json')) or \
         sorted(glob.glob(root + '/config/heroes/*.json'))
print("hero files:", [f.split('/')[-1] for f in hfiles][:8])
if hfiles:
    d = json.load(open(hfiles[0]))
    for k in list(d.keys())[:4]:
        e = d[k]
        print(k, '->', json.dumps({f: e.get(f) for f in ('index', 'shortIdentifier', 'class', 'special') if f in e}, ensure_ascii=False)[:300])
