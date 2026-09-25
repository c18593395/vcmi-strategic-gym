#!/bin/bash
# 对比 01_duel vs 02_duel 的 ep_log（首拍 obs 非空率）+ 检查 duel 图 reset 路径
PYBIN="${PYBIN:-/home/administrator/vcmi-workspace/venv/bin/python3}"
$PYBIN - <<'PY'
import json, glob, os
base="${base:-/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps}"
# 找 duel 图
duel=[f for f in sorted(os.listdir(base)) if 'duel' in f and f.endswith('.vmap')]
print("duel maps:", duel)

# 检查最近 ep_log
eplogs=sorted(glob.glob('/tmp/hermes_ep_*.log'), key=os.path.getmtime, reverse=True)[:30]
from collections import Counter
c=Counter(); nz=Counter(); steps1=Counter()
for p in eplogs:
    try:
        txt=open(p,errors='replace').read()
    except: continue
    for l in txt.splitlines():
        if l.startswith('[EP_TIME]'):
            import re
            m=re.search(r'map=(\S+)', l)
            mapn=m.group(1) if m else '?'
            c[mapn]+=1
            s=re.search(r'steps=(\d+)', l)
            if s and s.group(1)=='1':
                steps1[mapn]+=1
    # obs 非空率: 读 traj
    tj=p.replace('.log','_traj.json')
    if os.path.exists(tj):
        try:
            d=json.load(open(tj))
            import numpy as np
            if d.get('obs') and len(d['obs'])>0 and len(d['obs'][0])>30:
                nzv=int(np.count_nonzero(d['obs'][0]))
                nz["map??"]+=0
        except: pass
print("\n=== 最近 30 个 ep_log 的 EP_TIME 统计 ===")
for k,v in c.most_common():
    print(f"  {k}: 总{v}局, steps=1异常 {steps1.get(k,0)}局")
PY
