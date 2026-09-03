#!/bin/bash
F=/tmp/hermes_ep_11638.log
echo "=== TOWN/CAPTURE 事件:"
grep -E 'TOWN_CAPTURE|\[TOWN\]' "$F" | tail -8
echo "=== 该局 ep 结果:"
grep -E 'ep_steps' "$F" | tail -2
echo "=== 主日志最新进度:"
tail -3 /mnt/d/Bigdata/hero3_fresh/train_loop.log
