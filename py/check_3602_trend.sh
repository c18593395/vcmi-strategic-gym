#!/bin/bash
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
SEG=$(tail -n +$LINE "$LOG")
echo "=== 36X36_02 (调守卫) 局分布:"
echo "$SEG" | grep 'map=T05_adventure_36X36_02' | grep -oE 'ep_steps=[0-9]+ r=[0-9.-]+' | sort | uniq -c
echo
echo "=== avg_r 轨迹 (每 10 ep 抽样):"
echo "$SEG" | grep -oE 'step[0-9]+ avg_r=[0-9.-]+' | awk 'NR%10==1' | tail -15
echo
echo "=== 事件计数:"
printf "GUARD: %s  GUARD_DONE: %s  MINE: %s  TOWN: %s  TOWN_CAPTURE: %s  RECRUITED: %s  ZOMBIE: %s  RouterEx: %s  200步局: %s\n" \
  "$(echo "$SEG" | grep -c '\[GUARD\]')" "$(echo "$SEG" | grep -c 'GUARD_DONE')" \
  "$(echo "$SEG" | grep -c '\[MINE\]')" "$(echo "$SEG" | grep -c '\[TOWN\]')" \
  "$(echo "$SEG" | grep -c 'TOWN_CAPTURE')" "$(echo "$SEG" | grep -c 'RECRUITED')" \
  "$(echo "$SEG" | grep -c 'ZOMBIE')" "$(echo "$SEG" | grep -c 'battleStart exception')" \
  "$(echo "$SEG" | grep -c 'ep_steps=200')"
echo
echo "=== 最高分局 TOP5:"
echo "$SEG" | grep 'ep_steps=' | grep -oE 'r=[0-9.-]+ map=[^ ]+' | sort -t= -k2 -rn | head -5
