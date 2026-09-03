#!/bin/bash
# 主日志: 最近一个 8 步短局的完整事件流 (ep_steps=8 行前 12 行)
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
grep -n 'ep_steps=8 ' "$LOG" | tail -1
N=$(grep -n 'ep_steps=8 ' "$LOG" | tail -1 | cut -d: -f1)
sed -n "$((N-12)),$((N))p" "$LOG"
