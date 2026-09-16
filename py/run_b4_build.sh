#!/usr/bin/env bash
# B4 构建: 同步 main.cpp (Windows 共享盘 → WSL 原生) + 独立 CMake 重编 (零 rel 写入)
set -u
SRC=/mnt/d/Bigdata/hero3_fresh/tools/h3m2vmap/main.cpp
DST=/home/administrator/vcmi-native/tools/h3m2vmap/main.cpp

echo "=== [1] sync main.cpp ==="
[ -f "$SRC" ] || { echo "SRC missing: $SRC"; exit 1; }
cp "$SRC" "$DST" || exit 1
# 改 .py/.cpp 后清 __pycache__ 惯例不适用 C++, 但确认时间戳
ls -la "$DST"

cd /home/administrator/vcmi-native/tools/h3m2vmap || exit 1
rm -rf build; mkdir -p build; cd build

echo "=== [2] cmake configure ==="
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo .. > cfg.log 2>&1 || { cat cfg.log; exit 1; }
echo "cmake configure OK"

echo "=== [3] build ==="
cmake --build . -j2 > build.log 2>&1
RC=$?
if [ $RC -ne 0 ]; then
  echo "BUILD FAILED:"
  grep -E 'error:|Error' build.log | head -30
  echo "---- tail build.log ----"
  tail -30 build.log
  exit 1
fi
echo "build OK, binary size: $(stat -c%s ./h3m2vmap) bytes"
