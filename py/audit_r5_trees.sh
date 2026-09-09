#!/bin/bash
# R5 双树分叉审计 — Windows vcmi/ 工作区 vs WSL vcmi-native 源码树
# 用法: wsl bash /mnt/d/Bigdata/hero3_fresh/py/audit_r5_trees.sh [文件列表文件]
# 输出: 每文件 diff 行数 (strip-trailing-cr), 0 = 语义一致
A=/mnt/d/Bigdata/hero3_fresh/vcmi
B=/home/administrator/vcmi-native
FILES="server/ML/ServerPlugin.cpp server/CGameHandler.cpp client/CServerHandler.cpp client/Client.cpp ML/strategic_state.cpp ML/strategic_state.h AI/Nullkiller2/AIGateway.cpp"
if [ -n "$1" ]; then FILES=$(cat "$1"); fi
for f in $FILES; do
  if [ ! -f "$A/$f" ] || [ ! -f "$B/$f" ]; then echo "$f : MISSING(one side)"; continue; fi
  n=$(diff --strip-trailing-cr "$A/$f" "$B/$f" | grep -c '^[<>]')
  echo "$f : $n"
done
