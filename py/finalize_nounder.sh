#!/usr/bin/env bash
# 最终落位: Ready or Not + Unexpected Inheritance 两张 nounder 图
# 1) strip probe_ror → ready_or_not_nounder_adventure.vmap
# 2) ui_raw_nounder_adventure → unexpected_inheritance_nounder_adventure.vmap (改名)
# 3) 清理: wdc 全链产物 (弃用, red 主城在地下) + probe 中间件
set -u
cd /mnt/d/Bigdata/hero3_fresh
echo "=== 1) strip Ready or Not ==="
python3 py/strip_underground_vmap.py maps/h3m_to_vmap/probe_ror.vmap | grep -E 'objects_|selfcheck|output:|player_pos'
mv maps/h3m_to_vmap/probe_ror_nounder_adventure.vmap maps/h3m_to_vmap/ready_or_not_nounder_adventure.vmap
echo "=== 2) ui 改名 ==="
mv maps/h3m_to_vmap/ui_raw_nounder_adventure.vmap maps/h3m_to_vmap/unexpected_inheritance_nounder_adventure.vmap
echo "=== 3) 清理 wdc + probe 中间件 ==="
rm -f maps/training/when_dragons_clash_nounder_adventure.vmap \
      /home/administrator/vcmi-native/rel/bin/data/Maps/when_dragons_clash_nounder_adventure.vmap \
      maps/h3m_to_vmap/wdc_raw.vmap maps/h3m_to_vmap/wdc_raw_nounder_adventure.vmap \
      maps/h3m_to_vmap/probe_dl.vmap maps/h3m_to_vmap/probe_uu.vmap \
      maps/h3m_to_vmap/probe_fa_raw.vmap maps/h3m_to_vmap/fae_raw.vmap
echo "=== 4) 部署 maps/training/ + rel/bin ==="
for m in ready_or_not_nounder_adventure unexpected_inheritance_nounder_adventure; do
  cp "maps/h3m_to_vmap/$m.vmap" "maps/training/$m.vmap"
  cp "maps/h3m_to_vmap/$m.vmap" "/home/administrator/vcmi-native/rel/bin/data/Maps/$m.vmap"
  echo "deployed: $m maps/training=$(stat -c%s "maps/training/$m.vmap")B rel=$(stat -c%s "/home/administrator/vcmi-native/rel/bin/data/Maps/$m.vmap")B"
done
ls -la maps/training/*nounder* 2>/dev/null
