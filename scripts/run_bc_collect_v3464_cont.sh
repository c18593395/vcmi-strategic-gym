#!/bin/bash
# H.8 BC 重采集续采脚本 v2 (3464 维, 从 ep24 续采, NK2 对手)
# v1 坑: --episode 单局模式不接受 "|" 分隔多图参数 (Bad value for map), 必须单图
cd /mnt/d/Bigdata/hero3_fresh
MAPS=("Dungeon Keeper.h3m" "Key to Victory.h3m" "Good Witch, Bad Witch.h3m" "Fort Noxis.h3m")
for ep in $(seq 24 41); do
  idx=$((ep % 4))
  cur_map="${MAPS[$idx]}"
  echo "=== 启动局 $ep ($cur_map) ===" >> bc_data/bc_collect_v3464.log
  python3 -u collect_bc.py \
    --episode $ep \
    --map "$cur_map" \
    --max_pairs 200 \
    --out /mnt/d/Bigdata/hero3_fresh/bc_data/bc_raw_v3464.npz \
    --boot_timeout 240 --vcmi_timeout 240 --wait_timeout 90 \
    >> bc_data/bc_collect_v3464.log 2>&1
  echo "=== 局 $ep 子进程结束, 继续下一局 ===" >> bc_data/bc_collect_v3464.log
done
# 汇总
python3 - << 'EOF'
import numpy as np, glob
files = sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/bc_data/bc_raw_v3464_ep*.npz'))
total = 0
for f in files:
    d = np.load(f)
    total += len(d['obs'])
print(f"TOTAL {total} pairs across {len(files)} episodes")
EOF
