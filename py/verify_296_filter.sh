#!/bin/bash
# #296 降噪重启后验证 (2026-09-23)
set -u
echo "=== 训练进程状态 ==="
systemctl is-active homm3-train-v5 2>/dev/null
ps -ef | grep -E 'ep_runner|train_wsl2_ppo_v2' | grep -v grep
echo ""
f=$(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -1)
echo "=== 最新 hermes 日志: $f ==="
echo "mtime: $(stat -c '%y' "$f" 2>/dev/null)"
echo "Cannot answer 行数: $(grep -c 'Cannot answer the query -1' "$f" 2>/dev/null)"
echo ""
echo "=== hermes 日志最后 15 行 (应无 Cannot answer) ==="
tail -15 "$f" 2>/dev/null
echo ""
echo "=== 主日志最后 5 行 ==="
tail -5 /mnt/d/Bigdata/hero3_fresh/train_loop.log 2>/dev/null
