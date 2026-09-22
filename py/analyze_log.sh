#!/bin/bash
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
echo '=== 最近 5 条 ZOMBIE ==='
grep -n 'ZOMBIE' "$LOG" | tail -n 5
echo '=== 大额负奖励统计 (按 r= 数值) ==='
grep -oE 'r=-[0-9]+\.[0-9]+' "$LOG" > /tmp/r_neg.txt
awk -F'=' '{v=$2+0; if (v<-100) c1++; else c2++} END {print "r<-100:", c1; print "-100<=r<0:", c2}' /tmp/r_neg.txt
echo '=== 最近 8 条 ep (含 r=) ==='
grep -E 'ep_steps=' "$LOG" | grep -E 'r=-?[0-9]+\.[0-9]+' | tail -n 8 | grep -oE 'step[0-9]+ avg_r=[0-9.]+ ep=[0-9]+'
echo '=== 大额负奖励 ep 的 map 分布 ==='
grep -oE 'r=-[0-9]+\.[0-9]+ .*' "$LOG" | grep -oE 'map=T[0-9]+[a-zA-Z0-9_]*\.vmap' | sort | uniq -c | sort -rn
