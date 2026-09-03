#!/bin/bash
# R6 冒烟深度验证 v2
F=/tmp/hermes_ep_11638.log
N=$(grep -n 'BattleProcessor::startBattle DONE' "$F" | head -1 | cut -d: -f1)
echo "=== battleStart 行号: $N  (文件总行 $(wc -l < "$F"))"
echo "=== 战斗段 (startBattle 前 3 行到后 45 行, 去空行):"
sed -n "$((N-3)),$((N+45))p" "$F" | grep -vE '^\s*$'
echo
echo "=== 文件中 battle 相关全部行:"
grep -nE 'battle' "$F" | grep -viE 'popIfTop|stack:|Top Query|onExposure|notifyObject' | head -20
