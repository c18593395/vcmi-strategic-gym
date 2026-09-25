#!/bin/bash
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
echo "=== resume 后日志尾部 15 行:"
tail -n +$LINE "$LOG" | tail -15
echo
echo "=== 最新 hermes:"
F=$(ls -t /tmp/hermes_ep_*.log | head -1)
echo "$F ($(stat -c %y "$F" | cut -d. -f1))"
tail -5 "$F"
