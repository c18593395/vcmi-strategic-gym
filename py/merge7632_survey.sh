#!/bin/bash
# 评估 Nullkiller2 Pathfinding 子目录的本地改动量 (PR#7632 合并风险预检)
cd /home/administrator/vcmi-native
echo '--- Nullkiller2 本地 commit 总数 (自 clone) ---'
git log --oneline -- AI/Nullkiller2/ | wc -l
echo '--- Pathfinding 子目录本地 commit 数 ---'
git log --oneline -- AI/Nullkiller2/Pathfinding/ | wc -l
echo '--- Pathfinding 最近 10 条 commit ---'
git log --oneline -- AI/Nullkiller2/Pathfinding/ | head -10
echo '--- PR#7632 涉及的 Pathfinding 文件本地专属 commit 数 ---'
for f in AINodeStorage.cpp AINodeStorage.h Actors.cpp Actors.h AIPathfinder.cpp AIPathfinder.h GraphPaths.cpp GraphPaths.h ObjectGraph.cpp ObjectGraphCalculator.cpp Engine/Nullkiller.cpp; do
  n=$(git log --oneline -- "AI/Nullkiller2/Pathfinding/$f" 2>/dev/null | wc -l)
  echo "$f: $n"
done
echo '--- PR#7632 涉及的引擎文件本地改动 ---'
for f in lib/bonuses/Bonus.cpp lib/serialization/JsonDeserializer.cpp; do
  n=$(git log --oneline -- "$f" 2>/dev/null | wc -l)
  echo "$f: $n"
done
