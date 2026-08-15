#!/bin/bash
# H.8 BC 重采集启动脚本 (3464 维, 24 局, NK2 对手)
cd /mnt/d/Bigdata/hero3_fresh
rm -f bc_data/bc_raw_v3464_ep*.npz
exec python3 -u collect_bc.py \
  --map "Dungeon Keeper.h3m|Key to Victory.h3m|Good Witch, Bad Witch.h3m|Fort Noxis.h3m" \
  --episodes 24 --max_pairs 200 \
  --out bc_data/bc_raw_v3464.npz --watchdog 900 \
  > bc_data/bc_collect_v3464.log 2>&1
