#!/bin/bash
# T06 守卫战斗真伪统计 — 逐局: [GUARD] 事件数 + 引擎 CGCreature::battleFinished 次数 + 城布局识别
for f in $(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -60); do
  g=$(grep -c 'GUARD. guard' "$f" 2>/dev/null)
  b=$(grep -c 'CGCreature::battleFinished' "$f" 2>/dev/null)
  tw=$(grep -m1 'towns=\[' "$f" 2>/dev/null | grep -oc 'o[01]@')
  echo "$(basename $f) guard=$g engine_battle=$b towns=$tw"
done
