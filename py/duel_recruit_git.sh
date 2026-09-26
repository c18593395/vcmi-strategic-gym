#!/bin/bash
# 定谳: case16-18 现行代码体 + 892343da 可恢复性
AAI=/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp
echo "===== [1] AAI.cpp case 16-18 完整代码体 (L238-290) ====="
sed -n '238,290p' "$AAI"
echo
echo "===== [2] 892343da 对象是否还存在 (可恢复性) ====="
cd /home/administrator/vcmi-native
git cat-file -t 892343da 2>&1
echo
echo "===== [3] 若存在: 该 commit 改了什么 ====="
git show 892343da --stat 2>&1 | head -15
echo
echo "===== [4] 该 commit 的核心 diff (case16 段) ====="
git show 892343da 2>&1 | grep -A20 'case 16' | head -40
echo
echo "===== [5] 近 7 天 AAI.cpp 的提交史 ====="
git log --oneline --since='2026-09-20' -- AI/MMAI/AAI/AAI.cpp 2>&1 | head -8
echo
echo "===== [6] reflog 找 09-25 丢失点 ====="
git reflog 2>&1 | head -12
