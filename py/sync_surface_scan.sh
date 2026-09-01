#!/bin/bash
# 官方同步台账 - 本地分叉面扫描器 (在 WSL 中运行, 只读操作)
# 用法: wsl -e bash /mnt/d/Bigdata/hero3_fresh/py/sync_surface_scan.sh
# 输出: fork 基点 / 本地改动面按目录聚合 / 关键引擎文件本地改动量
cd /mnt/d/Bigdata/hero3_fresh/vcmi

echo '=== fork base (origin/develop snapshot) ==='
git log -1 --format='%h %ci %s' origin/develop

echo '=== merge-base with origin/develop ==='
git merge-base HEAD origin/develop || echo NONE

echo '=== local change surface: top-level dirs (files changed vs origin/develop) ==='
git diff --name-only origin/develop HEAD | sed 's|/.*||' | sort | uniq -c | sort -rn

echo '=== key engine files diff size vs origin/develop (+local mods) ==='
for f in \
  server/CGameHandler.cpp \
  server/BattleProcessor.h \
  lib/battle/BattleInfo.cpp \
  lib/battle/Unit.cpp \
  lib/serializer/JsonSerializer.cpp \
  lib/serializer/BinarySerializer.h \
  lib/pathfinder/CPathfinder.cpp \
  lib/mapObjects/CGTownInstance.cpp \
  lib/mapObjects/CGHeroInstance.cpp \
  lib/gameState/CGameState.cpp \
  lib/networkPacks/PacksForServer.h \
  ; do
  line=$(git diff --numstat origin/develop HEAD -- "$f" 2>/dev/null | head -1)
  if [ -z "$line" ]; then
    echo "$f: UNCHANGED"
  else
    echo "$f: +$(echo "$line" | awk '{print $1}') -$(echo "$line" | awk '{print $2}')"
  fi
done
