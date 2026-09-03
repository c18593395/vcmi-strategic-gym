#!/bin/bash
# P1e .so 同步 (运行时 -> 3 副本) + 源码双目录/Windows 镜像同步 + 清诊断日志
set -e
SRC=/home/administrator/vcmi-native/rel/bin/AI/libMMAI.so
for D in /home/administrator/vcmi-native-build/rel/bin/AI/libMMAI.so \
         /home/administrator/vtest/bin/AI/libMMAI.so \
         /home/administrator/vcmi-workspace/vcmi/rel/bin/AI/libMMAI.so; do
  cp "$SRC" "$D"
done
md5sum /home/administrator/vcmi-native/rel/bin/AI/libMMAI.so \
       /home/administrator/vcmi-native-build/rel/bin/AI/libMMAI.so \
       /home/administrator/vtest/bin/AI/libMMAI.so \
       /home/administrator/vcmi-workspace/vcmi/rel/bin/AI/libMMAI.so
cp /home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp /home/administrator/vcmi-native-build/AI/MMAI/AAI/AAI.cpp
cp /home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp /mnt/d/Bigdata/hero3_fresh/tools/patches_20260902/AAI.cpp
rm -f /tmp/rl_recruit_diag.log
echo SYNC_OK
