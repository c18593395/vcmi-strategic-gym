#!/bin/bash
echo "=== 时间: $(date +%H:%M:%S) 服务: $(systemctl --user is-active homm3-train-v5) ==="
echo "--- 引擎招兵诊断 (visit/tier) ---"
grep -E 'visit=|tier=' /tmp/rl_recruit_diag.log 2>/dev/null | tail -8
echo "--- RECRUITED (hermes) ---"
grep -h 'RECRUITED' /tmp/hermes_ep_*.log 2>/dev/null | tail -5
echo "--- 本 run 概览 ---"
L=$(grep -n 'Loaded train state' /mnt/d/Bigdata/hero3_fresh/train_loop.log | tail -1 | cut -d: -f1)
tail -n +$L /mnt/d/Bigdata/hero3_fresh/train_loop.log > /tmp/mon.log
echo "eps: $(grep -c 'avg_r=' /tmp/mon.log)"
grep -E 'avg_r=' /tmp/mon.log | tail -5
grep -oE '\[TOWN_BLOCKED\]|\[TOWNSTALL\]|\[TOWN_VISIT\]|\[TOWN\]|\[MINE\]|\[ZOMBIE\]' /tmp/mon.log | sort | uniq -c
