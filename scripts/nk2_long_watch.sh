#!/bin/bash
# NK2 长时内存实验: red=bc模型 + blue=NK2, 每30s采样 python 进程 RSS
LOG=/tmp/nk2_long_mem.log
echo "=== NK2 长时内存观测 $(date +%H:%M:%S) ===" > $LOG
for i in $(seq 1 30); do
  PID="${PID:-$(pgrep -f '^/home/administrator/vcmi-workspace/venv/bin/python' | head -1)}"
  if [ -n "$PID" ]; then
    RSS=$(ps -o rss= -p $PID 2>/dev/null | tr -d ' ')
    if [ -n "$RSS" ]; then RSS_MB=$((RSS/1024)); else RSS_MB="?"; fi
    DAY=$(grep -aoE 'day=[0-9]+' /tmp/nk2_long.log 2>/dev/null | tail -1)
    CHAIN=$(grep -ac 'Unable to complete chain' /tmp/nk2_long.log 2>/dev/null)
    MLW=$(grep -ac 'ML-wait' /tmp/nk2_long.log 2>/dev/null)
    echo "$(date +%H:%M:%S) pid=$PID rss=${RSS_MB}MB $DAY chain=$CHAIN mlwait=$MLW" >> $LOG
  else
    echo "$(date +%H:%M:%S) no_proc" >> $LOG
  fi
  sleep 30
done
echo "=== 观测完成 ===" >> $LOG
tail -40 $LOG
