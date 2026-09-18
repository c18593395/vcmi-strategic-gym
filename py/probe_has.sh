#!/usr/bin/env bash
# 探针: Hatchet Axe and Saw (2p 72x72 无地下)
set -u
cd /home/administrator/vcmi-native
BIN=tools/h3m2vmap/build/h3m2vmap
"$BIN" --save "rel/bin/data/Maps/Hatchet Axe and Saw.h3m" \
  "/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/probe_has.vmap" --no-r1 >/dev/null 2>&1
echo "convert rc=$?"
cd /mnt/d/Bigdata/hero3_fresh
python3 py/strip_underground_vmap.py maps/h3m_to_vmap/probe_has.vmap --peek 2>&1 | grep -E '===|objects: |mapLevels|surface 城|地下城|mainTown|死门'
