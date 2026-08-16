#!/bin/bash
# NK2 内存观测: 每 20s 采样采集子进程 RSS/VSZ + chain 错误计数
LOG=/tmp/nk2_mem_watch.log
echo "=== NK2 内存观测 (每20s) $(date +%H:%M:%S) ===" > $LOG
for i in $(seq 1 45); do
  PID=$(pgrep -f 'collect_bc.py --episode' | head -1)
  if [ -n "$PID" ]; then
    RSS=$(ps -o rss= -p $PID 2>/dev/null | tr -d ' ')
    VSZ=$(ps -o vsz= -p $PID 2>/dev/null | tr -d ' ')
    if [ -n "$RSS" ]; then RSS_MB=$((RSS/1024)); else RSS_MB="?"; fi
    if [ -n "$VSZ" ]; then VSZ_MB=$((VSZ/1024)); else VSZ_MB="?"; fi
    # chain 错误计数: 采集日志 + 可能的 vcmiserver 输出
    CHAIN=$(grep -rc 'Unable to complete chain' /mnt/d/Bigdata/hero3_fresh/bc_data/bc_collect_v3464_fix.log 2>/dev/null | awk -F: '{s+=$2} END {print s+0}')
    SAVED=$(grep -c 'SAVED' /mnt/d/Bigdata/hero3_fresh/bc_data/bc_collect_v3464_fix.log 2>/dev/null)
    echo "$(date +%H:%M:%S) pid=$PID rss=${RSS_MB}MB vsz=${VSZ_MB}MB saved_ep=$SAVED chain_err=$CHAIN" >> $LOG
  else
    echo "$(date +%H:%M:%S) no_collect_proc" >> $LOG
  fi
  sleep 20
done
echo "=== 观测完成 ===" >> $LOG
tail -50 $LOG
