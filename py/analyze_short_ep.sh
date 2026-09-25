#!/bin/bash
# 短局 (8步) 结束原因分析
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
echo "=== 主日志 resume 后的 ZOMBIE/死亡行:"
tail -n +$LINE "$LOG" | grep -iE 'ZOMBIE|dead|blocked x2' | tail -6
echo
echo "=== 最近 3 个 hermes 文件的死亡/结束痕迹:"
for F in $(ls -t /tmp/hermes_ep_*.log | head -3); do
  echo "--- $F ($(stat -c %y "$F" | cut -d. -f1))"
  grep -iE 'ZOMBIE|dead \(|all-blocked' "$F" | tail -3
  grep -cE 'battleStart exception' "$F"
  grep -E 'BattleProcessor::startBattle DONE' "$F" | wc -l
  grep -E 'ep_steps' "$F" | tail -1
done
echo
echo "=== 战斗后行为: battleFinished 之后的 TOWN/CAPTURE 事件 (最近文件):"
F=$(ls -t /tmp/hermes_ep_*.log | head -1)
grep -E 'battleFinished RETURN|TOWN_CAPTURE|\[TOWN\]' "$F" | tail -8
