#!/bin/bash
# R5 大文件差异关键词过滤 — 只显示功能性差异 (ML/ENGINE/打点/fix 标记)
A=/mnt/d/Bigdata/hero3_fresh/vcmi
B=/home/administrator/vcmi-native
for f in server/CGameHandler.cpp client/CServerHandler.cpp client/Client.cpp; do
  echo "======== $f ========"
  diff --strip-trailing-cr "$A/$f" "$B/$f" | grep '^[<>]' | grep -iE 'ML-|ML_|ENGINE|engine|打点|fprintf|dump|interfaceMutex|in_my_turn|endTurn|heroMoved|battleEnded|fix|HACK|ML |strategic' | head -40
  echo "--- 位移统计: diff 总块数 = $(diff --strip-trailing-cr "$A/$f" "$B/$f" | grep -c '^[0-9]')"
done
