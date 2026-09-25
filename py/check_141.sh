#!/bin/bash
# 查 r=141.53 T04 局的事件构成 (确认 141 分来源)
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
grep -n 'ep_steps=73 r=141.53' "$LOG" | tail -3
N=$(grep -n 'ep_steps=73 r=141.53' "$LOG" | tail -1 | cut -d: -f1)
echo "=== 最近一局 141.53 的前 90 行事件流:"
sed -n "$((N-90)),$((N))p" "$LOG" | grep -E '\[GUARD\]|\[MINE\]|\[TOWN\]|\[TOWN_CAPTURE\]|\[START_HOME\]|\[TOWN_VISIT\]|\[RECRUITED\]|\[TOWNSTALL\]|\[ZOMBIE\]' | head -30
echo
echo "=== 该局 map 与 obs_nz:"
sed -n "$((N))p" "$LOG" | grep -oE 'map=[^ ]+|obs_nz=[0-9]+'
