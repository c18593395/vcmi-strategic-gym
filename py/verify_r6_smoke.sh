#!/bin/bash
# R6 冒烟深度验证: 战斗期间 BAI 动作流 (MLBot/allowMlBot/Python 回调痕迹)
F=/tmp/hermes_ep_11638.log
echo "=== 战斗段完整日志 (battleStart 前后各 30 行):"
N=$(grep -n 'BattleProcessor::startBattle DONE' "$F" | head -1 | cut -d: -f1)
if [ -n "$N" ]; then
  sed -n "$((N-5)),$((N+40))p" "$F" | grep -vE '^\s*$' | head 45
fi
echo
echo "=== 战斗动作/MLBot 痕迹:"
grep -icE 'mlbot|allowMlBot|battle.*action|action.*battle' "$F"
grep -iE 'in_battle|yourTurn' "$F" | tail -5
