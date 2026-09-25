#!/usr/bin/env bash
# R2v2 三类图实测: 查 report R2v2_* 键 + ROUNDTRIP
set -u
cd /home/administrator/vcmi-native
BIN=tools/h3m2vmap/build/h3m2vmap
declare -A MAPS=(
  [faeries]="Faeries"                          # 2p, 对手 pink
  [ror]="Ready or Not"                          # 3p, 第三家 tan (上次崩)
  [ui]="Unexpected Inheritance"                 # 2p, 对手 blue (基线)
)
for k in faeries ror ui; do
  n="${MAPS[$k]}"
  out="${out:-/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/r2v2_${k}.vmap}"
  "$BIN" --save "rel/bin/data/Maps/$n.h3m" "$out" --no-r1 >/dev/null 2>&1
  rc=$?
  echo "=== $n rc=$rc ==="
  python3 -c "import json;r=json.load(open('/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/report.json'));print({k2:v for k2,v in r.items() if 'R2v2' in k2 or k2 in ('R4_kept','R4_removed')})" 2>/dev/null
done
