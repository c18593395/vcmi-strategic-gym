#!/usr/bin/env bash
# 探针: Gorlam's Tentacle Swampland (2p 有地下, 72x72)
set -u
cd /home/administrator/vcmi-native
BIN=tools/h3m2vmap/build/h3m2vmap
"$BIN" --save "rel/bin/data/Maps/Gorlam's Tentacle Swampland.h3m" \
  "/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/probe_gorlam.vmap" --no-r1 >/dev/null 2>&1
echo "convert rc=$?"
cd /mnt/d/Bigdata/hero3_fresh
python3 py/strip_underground_vmap.py maps/h3m_to_vmap/probe_gorlam.vmap --peek 2>&1 | grep -E '===|objects: |surface 城|地下城|mainTown|死门'
