#!/usr/bin/env bash
# B3 验证: 独立 CMake 工程编译 h3m2vmap + 各规则开关对账
set -u
cd /home/administrator/vcmi-native/tools/h3m2vmap 2>/dev/null || exit 1
rm -rf build; mkdir -p build; cd build

echo "=== [1] cmake configure ==="
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo .. > cfg.log 2>&1 || { cat cfg.log; exit 1; }
echo "cmake configure OK"

echo "=== [2] build ==="
cmake --build . -j2 > build.log 2>&1
RC=$?
if [ $RC -ne 0 ]; then
  echo "BUILD FAILED:"
  grep -E 'error:|Error' build.log | head -30
  echo "---- tail build.log ----"
  tail -30 build.log
  exit 1
fi
echo "build OK, binary size: $(stat -c%s ./h3m2vmap 2>/dev/null || ls -la h3m2vmap | awk '{print $5}') bytes"

# 让 build/h3m2vmap 运行时找到 rel 系 .so
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:${LD_LIBRARY_PATH:-}

KNEE="/home/administrator/vcmi-native/data/Maps/Knee Deep in the Dead.h3m"
[ -f "$KNEE" ] || KNEE="/home/administrator/vcmi-native/rel/bin/data/Maps/Knee Deep in the Dead.h3m"
OUT=/tmp/b3_rules_test.vmap
rm -f "$OUT" /tmp/report.json

echo "=== [3] run: all B3 rules ==="
./h3m2vmap --save "$KNEE" "$OUT" \
  --r3_scale 1.5 \
  --map-name "P10_B3_KneeDeep_R3_150" 2>&1 | tail -40
echo "RC=${PIPESTATUS[0]}"
