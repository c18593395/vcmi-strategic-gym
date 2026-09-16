#!/usr/bin/env bash
# B3 全规则 + 各开关对账 (需 cd 到 vcmi-native 根, config/ 才能被引擎找到)
set -u
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:${LD_LIBRARY_PATH:-}
BIN=/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap
KNEE="/home/administrator/vcmi-native/data/Maps/Knee Deep in the Dead.h3m"
[ -f "$KNEE" ] || KNEE="/home/administrator/vcmi-native/rel/bin/data/Maps/Knee Deep in the Dead.h3m"
# 必须 cd 到 vcmi-native 根, 引擎 loadFilesystem 才能找到 config/ 子目录
cd /home/administrator/vcmi-native

echo "=== [1] all B3 rules (r3_scale=1.5) ==="
rm -f /tmp/b3_rules_test.vmap /tmp/report.json
$BIN --save "$KNEE" /tmp/b3_rules_test.vmap --r3_scale 1.5 --map-name "P10_B3_KneeDeep_R3_150" 2>&1
RC=$?
echo "RC=$RC"
[ -f /tmp/report.json ] && { echo "--- report.json ---"; cat /tmp/report.json; }
[ -f /tmp/b3_rules_test.vmap ] && echo "OUT size: $(stat -c%s /tmp/b3_rules_test.vmap) bytes"
