#!/bin/bash
# batch1 剩余 3 张捕获: 出现即记录, 全部齐或 3 小时超时退出 (09-22)
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
OUT=/tmp/_b1_rest.txt
START_LINE=$(grep -n 'WSL2 PPO v2' $LOG | tail -1 | cut -d: -f1)
DEADLINE=$(( $(date +%s) + 10800 ))
while true; do
  : > $OUT
  for M in good_to_go judgement_day elbow_room; do
    L=$(tail -n +$START_LINE $LOG | grep -aE "EP_TIME\] map=${M}_h3m\.vmap " | tail -1)
    if [ -n "$L" ]; then
      echo "[$M] $L" >> $OUT
    else
      echo "[$M] 未出现" >> $OUT
    fi
  done
  NB=$(tail -n +$START_LINE $LOG | grep -acE "EP_TIME\] map=(good_to_go|judgement_day|elbow_room)_h3m\.vmap ")
  echo "captured=$NB/3  $(date +%T)" >> $OUT
  if [ "$NB" -ge 3 ]; then
    echo ALL-THREE-CAPTURED >> $OUT
    break
  fi
  if [ $(date +%s) -gt $DEADLINE ]; then
    echo TIMEOUT-3H >> $OUT
    break
  fi
  sleep 300
done
