#!/bin/bash
# 判据①④精确统计
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
SEG=$(tail -n +$LINE "$LOG")
echo "=== 判据①: 各 T05 图高分局 (r>=120) 数:"
for M in T05_adventure_36X36_01 T05_adventure_52X52_01 T05_adventure_52X52_02; do
  C=$(echo "$SEG" | grep "map=$M.vmap" | grep -oE 'r=[0-9.-]+' | awk -F= '$2>=120' | wc -l)
  T=$(echo "$SEG" | grep -c "map=$M.vmap")
  echo "  $M: 高分局 $C / 总局 $T"
done
echo
echo "=== 判据④: 大额负局 (r<-150):"
echo "$SEG" | grep 'ep_steps=' | grep -oE 'r=[0-9.-]+' | awk -F= '$2<-150' | wc -l
echo
echo "=== T04_mir 高分局 (自发信号佐证):"
for M in 20X20_03_mir 20X20_04_mir 30X30_03_mir 30X30_04_mir 36X36_03_mir 36X36_04_mir; do
  C=$(echo "$SEG" | grep "map=T04_adventure_$M" | grep -oE 'r=[0-9.-]+' | awk -F= '$2>=60' | wc -l)
  echo "  $M: r>=60 局 $C"
done
