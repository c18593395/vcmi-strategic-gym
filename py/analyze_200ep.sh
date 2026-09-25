#!/bin/bash
# 200 步挂死局专项分析: T05 r=-126 局
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
echo "=== 定位 r=-126 局的 ep_steps 行号:"
grep -n 'ep_steps=200 r=-126' "$LOG" | tail -2
N=$(grep -n 'ep_steps=200 r=-126' "$LOG" | tail -1 | cut -d: -f1)
echo
echo "=== 该局完整事件流 (前 60 行到 ep_steps 行):"
sed -n "$((N-60)),$((N))p" "$LOG"
echo
echo "=== 该局 act 序列:"
sed -n "$((N))p" "$LOG" | grep -oE 'act=\[[^]]*\]'
