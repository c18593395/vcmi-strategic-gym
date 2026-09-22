#!/bin/bash
# P10-B2: 部署 King of Pain.vmap 到训练池的三个 vmap 目录
# 命名保留原 H3M 名, 便于溯源
set -e

SRC=/home/administrator/vcmi-native/rel/bin/data/Maps/vmap_from_h3m/King\ of\ Pain.h3m.vmap

# 1) ep_runner 直接读取: maps/training/
mkdir -p /mnt/d/Bigdata/hero3_fresh/maps/training
cp -v "$SRC" "/mnt/d/Bigdata/hero3_fresh/maps/training/King of Pain.h3m.vmap"

# 2) 引擎数据目录: vcmi/data/Maps/
mkdir -p /mnt/d/Bigdata/hero3_fresh/vcmi/data/Maps
cp -v "$SRC" "/mnt/d/Bigdata/hero3_fresh/vcmi/data/Maps/King of Pain.h3m.vmap"

# 3) vcmi_gym env v13: vcmi_gym/envs/v13/maps/
mkdir -p /mnt/d/Bigdata/hero3_fresh/vcmi_gym/envs/v13/maps
cp -v "$SRC" "/mnt/d/Bigdata/hero3_fresh/vcmi_gym/envs/v13/maps/King of Pain.h3m.vmap"

echo "---- 校验 ----"
ls -la "/mnt/d/Bigdata/hero3_fresh/maps/training/King of Pain.h3m.vmap" \
      "/mnt/d/Bigdata/hero3_fresh/vcmi/data/Maps/King of Pain.h3m.vmap" \
      "/mnt/d/Bigdata/hero3_fresh/vcmi_gym/envs/v13/maps/King of Pain.h3m.vmap"
