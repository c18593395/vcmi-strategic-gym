#!/bin/bash
# 查 MIX 实际状态 + 池目录候选图可用性
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
IDX=/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/_pool_index.json
POOLDIR=/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool

echo "=== 当前 step / active / MainPID ==="
grep -oE 'step[0-9]+ avg_r=' "$LOG" | tail -1
systemctl is-active homm3-train-v5
systemctl show -p MainPID --value homm3-train-v5
echo

echo "=== 重启后 [MIX_TRACE] 统计 ==="
# 取最后一次 MIX_TRACE 的 ep 作为重启后起点：直接统计全部 MIX_TRACE（重启前打点未生效，0 条也无妨）
echo -n "MIX_TRACE 总行数: "
grep -c 'MIX_TRACE' "$LOG"
echo -n "  其中 hit=True: "
grep 'MIX_TRACE' "$LOG" | grep -c 'hit=True'
echo -n "  其中 hit=False: "
grep 'MIX_TRACE' "$LOG" | grep -c 'hit=False'
echo "  hit=True 的图:"
grep 'MIX_TRACE' "$LOG" | grep 'hit=True' | grep -oE 'map=[^ ]+' | sort | uniq -c
echo
echo "  最近 8 条 MIX_TRACE:"
grep 'MIX_TRACE' "$LOG" | tail -8
echo

echo "=== 池目录可用性（候选图实际存在?）==="
echo -n "h3m_pool .vmap 总数: "
ls "$POOLDIR"/*.vmap 2>/dev/null | wc -l
echo "batch=1/2/99 图是否在池目录:"
python3 << 'PY'
import json, os
idx = json.load(open('/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/_pool_index.json'))
pdir = '/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool'
for tgt in (1,2,3):
    ks = [k for k,v in idx.items()
          if (v or {}).get('batch')==tgt and (v or {}).get('blue_ai')!='skip']
    exist = [k for k in ks if os.path.exists(os.path.join(pdir,k))]
    missing = [k for k in ks if not os.path.exists(os.path.join(pdir,k))]
    print(f"  batch={tgt}: index={len(ks)} in_dir={len(exist)} missing={len(missing)}")
    for k in exist:
        print(f"      ✓ {k} (reason={ (idx.get(k) or {}).get('reason','') })")
    for k in missing:
        print(f"      ✗ MISSING {k}")
PY
