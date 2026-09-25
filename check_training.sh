#!/bin/bash
# 检查训练进展
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"

if [ ! -f "$LOG" ]; then
  echo "[NO LOG] training not started yet"
  exit 0
fi

# 最新step日志
LAST_LINE=$(tail -1 "$LOG")
echo "=== HoMM3 Training Status ==="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"

# 检查进程
if pgrep -f train_wsl2_ppo > /dev/null 2>&1; then
  echo "Status: RUNNING"
else
  echo "Status: NOT RUNNING (check train_loop.sh)"
fi

# 提取最新训练输出
LAST_STEP=$(grep "step" "$LOG" | tail -1)
EP_TOTAL=$(grep "ep=" "$LOG" | wc -l)
echo "Episodes completed: $EP_TOTAL"
if [ -n "$LAST_STEP" ]; then
  echo "Latest: $LAST_STEP"
fi

# 提取总耗时
TOTAL_TIME=$(grep "DONE" "$LOG" | tail -1)
if [ -n "$TOTAL_TIME" ]; then
  echo "Last round: $TOTAL_TIME"
fi

# 日志大小
echo "Log size: $(wc -c < "$LOG") bytes"
echo "=============================="
