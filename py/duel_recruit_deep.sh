#!/bin/bash
# 深挖: ① force game_over winner 归属 ② WSL .so 是否含 09-25 dst=cur 修复
LOG=/tmp/duel_smoke_1.log
echo "===== [A] force game_over winner ====="
grep -E 'force game_over|winner' "$LOG" | head -5
echo
echo "===== [B] 局末 -200 败北信号 (blue 胜 = red 败) ====="
grep -E 'game_over=2|game_over=1|r=-2[0-9][0-9]|victory|defeat' "$LOG" | head -8
echo
echo "===== [C] WSL vcmi-native 源码: AAI.cpp case16-18 是否有 dst=cur 修复 ====="
AAI=$(find /home/administrator/vcmi-native -name 'AAI.cpp' -path '*MMAI*' 2>/dev/null | head -1)
[ -z "$AAI" ] && AAI=$(find /home/administrator/vcmi-native -name 'AAI.cpp' 2>/dev/null | head -1)
echo "AAI.cpp: $AAI"
if [ -n "$AAI" ]; then
  ls -l "$AAI"
  echo "--- case 16-18 段 (recruit dst 逻辑) ---"
  grep -n -A3 'case 16' "$AAI" | head -25
  echo "--- getUpperArmy / moveHero-进城 修复痕迹 ---"
  grep -cn 'getUpperArmy' "$AAI"
  grep -n 'dst *= *cur\|dst=cur\|// 09-25' "$AAI" | head -8
fi
echo
echo "===== [D] .so 与源码时间戳对照 (重编是否覆盖 AAI 改动) ====="
SO=/home/administrator/vcmi-native/rel/bin/libmlclient.so
ls -l "$SO"
echo
echo "===== [E] .so 内 09-25 修复特征串 (nm/strings 抽查) ====="
nm -D "$SO" 2>/dev/null | grep -cE 'strategic_state_force_game_over'
strings "$SO" 2>/dev/null | grep -cE 'ML-fix|force game_over'
echo
echo "===== [F] WSL vcmi-native git 状态 (892343da 是否在 HEAD 祖先) ====="
cd /home/administrator/vcmi-native 2>/dev/null && git log --oneline -5 2>/dev/null && git branch --contains 892343da 2>/dev/null | head -3 || echo "(git 查询失败或非 git 树)"
