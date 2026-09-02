#!/bin/bash
# vmap2h3m 双图转换 + 读回对账
set -u
cd /mnt/d/Bigdata/hero3_fresh
for m in T04_adventure_36X36_02 T03_adventure_30X30_01; do
    echo "== $m"
    python3 py/vmap2h3m.py "/home/administrator/vcmi-native/rel/bin/data/Maps/${m}.vmap" "/tmp/${m}.h3m" > "/tmp/v2h_${m}.log" 2>&1
    echo "convert exit=$?"
    tail -3 "/tmp/v2h_${m}.log"
    echo "-- readback:"
    python3 scripts/h3m_tool.py objects "/tmp/${m}.h3m" 2>&1 | tail -11
done
