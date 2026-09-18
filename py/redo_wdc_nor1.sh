#!/usr/bin/env bash
# WDC no-r1 重转 + strip + 部署 (最后候选: red 无地表城, 赌 mainTown 生成点可站)
set -u
cd /home/administrator/vcmi-native
BIN=tools/h3m2vmap/build/h3m2vmap
"$BIN" --save "rel/bin/data/Maps/When Dragons Clash.h3m" \
  "/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/wdc_raw.vmap" --no-r1 >/dev/null 2>&1
echo "convert rc=$?"
cd /mnt/d/Bigdata/hero3_fresh
python3 py/strip_underground_vmap.py maps/h3m_to_vmap/wdc_raw.vmap | grep -E 'objects_kept|selfcheck'
mv maps/h3m_to_vmap/wdc_raw_nounder_adventure.vmap maps/h3m_to_vmap/when_dragons_clash_nounder_adventure.vmap
cp maps/h3m_to_vmap/when_dragons_clash_nounder_adventure.vmap maps/training/
cp maps/h3m_to_vmap/when_dragons_clash_nounder_adventure.vmap /home/administrator/vcmi-native/rel/bin/data/Maps/
echo "DEPLOY-OK $(stat -c%s maps/training/when_dragons_clash_nounder_adventure.vmap)B"
