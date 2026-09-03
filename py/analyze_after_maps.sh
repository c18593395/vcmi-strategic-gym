#!/bin/bash
# 加图后日志分析: 镜像图表现 vs 原图 / 固化是否破
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
SEG=$(tail -n +$LINE "$LOG")
echo "=== 加图后 ep 数:"
echo "$SEG" | grep -c 'ep_steps='
echo "$SEG" | grep -oE 'step[0-9]+ avg_r=[0-9.-]+' | tail -1
echo
echo "=== ep 明细 (图+结局):"
echo "$SEG" | grep 'ep_steps=' | sed -E 's/act=\[[^]]*\] //; s/obs_nz=[0-9]+ //' | tail -20
echo
echo "=== 唯一 (map,steps,r) 组合数 vs ep 数:"
echo "$SEG" | grep 'ep_steps=' | sed -E 's/act=\[[^]]*\] //; s/obs_nz=[0-9]+ //; s/ep_steps=//' | sort -u | wc -l
echo
echo "=== 事件计数:"
printf "TOWN visit: %s  TOWN_CAPTURE: %s  RECRUITED: %s  ZOMBIE: %s  RouterEx: %s  TOWNSTALL: %s\n" \
  "$(echo "$SEG" | grep -c '\[TOWN\]')" "$(echo "$SEG" | grep -c 'TOWN_CAPTURE')" \
  "$(echo "$SEG" | grep -c 'RECRUITED')" "$(echo "$SEG" | grep -c 'ZOMBIE')" \
  "$(echo "$SEG" | grep -c 'battleStart exception')" "$(echo "$SEG" | grep -c 'TOWNSTALL')"
echo
echo "=== act 分布:"
echo "$SEG" | grep -oE 'act=\[[^]]*\]' | tr -d 'act=[] ' | tr ',' '\n' | sort | uniq -c | sort -rn
echo
echo "=== 战斗事件 (最新 hermes):"
F=$(ls -t /tmp/hermes_ep_*.log | head -1)
grep -cE 'BattleProcessor::startBattle DONE' "$F" 2>/dev/null
grep -E 'battleFinished RETURN' "$F" 2>/dev/null | tail -3
