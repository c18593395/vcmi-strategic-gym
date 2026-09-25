#!/usr/bin/env bash
# 临时探针: 批量转换候选图 (no-r1) + 城/mainTown 层分布探测
set -u
cd /home/administrator/vcmi-native
BIN=tools/h3m2vmap/build/h3m2vmap
declare -A MAPS=(
  ["ror"]="Ready or Not"
  ["uu"]="Undead Unrest"
  ["dl"]="Divided Loyalties"
)
for k in ror uu dl; do
  n="${MAPS[$k]}"
  out="${out:-/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/probe_${k}.vmap}"
  "$BIN" --save "rel/bin/data/Maps/$n.h3m" "$out" --no-r1 >/dev/null 2>&1
  echo "converted: $n -> $(basename "$out") rc=$?"
done
cd /mnt/d/Bigdata/hero3_fresh
python3 py/strip_underground_vmap.py maps/h3m_to_vmap/probe_*.vmap --peek 2>&1 | grep -E '===|surface 城|地下城|mainTown|objects: '
