#!/bin/bash
# ckpt_watcher.sh — checkpoint 推送链路的 cron 触发器 (解耦, 不改动正在跑的 24/7 训练).
# 发现 checkpoints/ 下有比上次更新的 wsl2_ckpt_*.pt 就调用 ckpt_push_hook.py 打通整条链路.
#
# 安装 crontab (WSL2 内):
#   crontab -e
#   */15 * * * * /mnt/d/Bigdata/hero3_fresh/py/ckpt_watcher.sh >> /mnt/d/Bigdata/hero3_fresh/push_watcher.log 2>&1
#
# 或单次手动: bash ckpt_watcher.sh
set -u

CKPT_DIR=/mnt/d/Bigdata/hero3_fresh/checkpoints
MARKER=/mnt/d/Bigdata/hero3_fresh/.last_ckpt_pushed
HOOK=/mnt/d/Bigdata/hero3_fresh/py/ckpt_push_hook.py
VENV=/home/administrator/vcmi-workspace/venv/bin/python
HOOK_LOG=/mnt/d/Bigdata/hero3_fresh/push_hook.log

latest=$(ls -t "$CKPT_DIR"/wsl2_ckpt_*.pt 2>/dev/null | head -1)
[ -z "$latest" ] && { echo "[watcher $(date '+%F %T')] no checkpoint yet"; exit 0; }

base=$(basename "$latest")
last=$(cat "$MARKER" 2>/dev/null || true)
if [ "$base" = "$last" ]; then
  exit 0   # 已处理, 跳过
fi

echo "[watcher $(date '+%F %T')] NEW checkpoint: $base -> push"
"$VENV" "$HOOK" --ckpt "$latest" >> "$HOOK_LOG" 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then
  echo "$base" > "$MARKER"
  echo "[watcher] marked $base as pushed (rc=0)"
else
  echo "[watcher] hook rc=$rc, 不更新 marker, 下个周期重试"
fi
