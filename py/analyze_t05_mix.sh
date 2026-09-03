#!/bin/bash
# T05 混入后训练分析
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
SEG=$(tail -n +$LINE "$LOG")
echo "=== 本次启动 ep 数与进度:"
echo "$SEG" | grep -c 'ep_steps='
echo "$SEG" | grep -oE 'step[0-9]+ avg_r=[0-9.-]+ ep=[0-9]+' | tail -1
echo
echo "=== ep 明细 (图+结局, 最近 15):"
echo "$SEG" | grep 'ep_steps=' | sed -E 's/act=\[[^]]*\] //; s/obs_nz=[0-9]+ //' | tail -15
echo
echo "=== 关键事件计数:"
printf "GUARD战斗: %s  GUARD_DONE: %s  TOWN visit: %s  TOWN_CAPTURE: %s  RECRUITED: %s  ZOMBIE: %s  RouterEx: %s  TOWNSTALL: %s\n" \
  "$(echo "$SEG" | grep -c '\[GUARD\]')" "$(echo "$SEG" | grep -c 'GUARD_DONE')" \
  "$(echo "$SEG" | grep -c '\[TOWN\]')" "$(echo "$SEG" | grep -c 'TOWN_CAPTURE')" \
  "$(echo "$SEG" | grep -c 'RECRUITED')" "$(echo "$SEG" | grep -c 'ZOMBIE')" \
  "$(echo "$SEG" | grep -c 'battleStart exception')" "$(echo "$SEG" | grep -c 'TOWNSTALL')"
echo
echo "=== 图分布 (ep 计):"
echo "$SEG" | grep -oE 'map=[^ ]+' | sort | uniq -c | sort -rn
echo
echo "=== act 分布:"
echo "$SEG" | grep -oE 'act=\[[^]]*\]' | tr -d 'act=[] ' | tr ',' '\n' | sort | uniq -c | sort -rn
echo
echo "=== 唯一 (map,steps,r) 组合数:"
echo "$SEG" | grep 'ep_steps=' | sed -E 's/act=\[[^]]*\] //; s/obs_nz=[0-9]+ //; s/ep_steps=//' | sort -u | wc -l
