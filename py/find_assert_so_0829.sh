#!/bin/bash
# [DIAG-0829] 定位 'QueryID is -1' 断言字符串在哪个 .so
PAT='QueryID is -1'
for f in /home/administrator/vcmi-native/rel/bin/*.so \
         /home/administrator/vcmi-native/rel/bin/AI/*.so \
         /home/administrator/vcmi-native/build/bin/*.so \
         /home/administrator/rel-diag-bin/*.so; do
  [ -f "$f" ] || continue
  c=$(strings "$f" 2>/dev/null | grep -c "$PAT")
  [ "$c" != "0" ] && echo "HIT($c): $f"
done
echo '--- AI/MMAI 相关 .so (08-01 后修改) ---'
find /home/administrator/vcmi-native -name '*.so' -path '*AI*' -newermt 2026-08-01 2>/dev/null | head -8
echo '--- data/Mods 下 MMAI ---'
find /home/administrator/vcmi-native/data/Mods /home/administrator/.vcmi/Mods -name '*.so' 2>/dev/null | head -10
