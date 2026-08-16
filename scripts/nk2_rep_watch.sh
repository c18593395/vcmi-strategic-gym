#!/bin/bash
# NK2 内存复现实验观测: blue=NK2 + red=随机, 每20s采样
LOG=/tmp/nk2_rep_mem.log
echo "=== NK2 复现实验内存观测 $(date +%H:%M:%S) ===" > $LOG
for i in $(seq 1 30); do
  PID=$(pgrep -f 'vcmi-workspace/venv/bin/python' | head -1)
  if [ -n "$PID" ]; then
    RSS=$(ps -o rss= -p $PID 2>/dev/null | tr -d ' ')
    VSZ=$(ps -o vsz= -p $PID 2>/dev/null | tr -d ' ')
    if [ -n "$RSS" ]; then RSS_MB=$((RSS/1024)); else RSS_MB="?"; fi
    if [ -n "$VSZ" ]; then VSZ_MB=$((VSZ/1024)); else VSZ_MB="?"; fi
    CHAIN=$(grep -rc 'Unable to complete chain' /tmp/nk2_rep.log 2>/dev/null | awk -F: '{s+=$2} END {print s+0}')
    echo "$(date +%H:%M:%S) pid=$PID rss=${RSS_MB}MB vsz=${VSZ_MB}MB chain_err=$CHAIN" >> $LOG
  else
    echo "$(date +%H:%M:%S) no_runner_proc" >> $LOG
  fi
  sleep 20
done
echo "=== 观测完成 ===" >> $LOG
tail -40 $LOG
