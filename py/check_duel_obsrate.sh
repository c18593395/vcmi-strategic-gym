#!/bin/bash
# duel 图首局 obs 非空率 — 从最近 ep_log 提取 duel 局首拍 obs_nz
PYBIN=/home/administrator/vcmi-workspace/venv/bin/python3
$PYBIN - <<'PY'
import json, glob, os, re, collections
eplogs=sorted(glob.glob('/tmp/hermes_ep_*.log'), key=os.path.getmtime, reverse=True)
c=collections.Counter()  # map -> [nz0_count, total]
for p in eplogs:
    mapname=None
    for l in open(p, errors='replace'):
        m=re.search(r'map=(\S+\.vmap)', l)
        if m: mapname=m.group(1)
    if not mapname or 'duel' not in mapname: continue
    # 读 traj
    tj=p.replace('.log','_traj.json')
    if not os.path.exists(tj): continue
    try:
        d=json.load(open(tj))
        import numpy as np
        if d.get('obs') and len(d['obs'])>0:
            nz=int(np.count_nonzero(d['obs'][0]))
            c[mapname].setdefault(0,0)
            c[mapname][1]+=1
            if nz==0: c[mapname][0]+=1
    except Exception as e:
        pass
print("=== duel 图 首拍 obs 全空率 (最近 30 局) ===")
for k,v in sorted(c.items()):
    tot,zero=v[1],v[0]
    print(f"  {k}: obs全空 {zero}/{tot} 局")
PY
