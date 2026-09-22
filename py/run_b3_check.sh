#!/usr/bin/env bash
# 打印 Knee Deep 图中所有对象的 getTypeName()
set -u
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:${LD_LIBRARY_PATH:-}
cd /home/administrator/vcmi-native
/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap --check-h3m "data/Maps/Knee Deep in the Dead.h3m" 2>&1 | grep -E "IN|objects=|ENGINE|error" | head -5
