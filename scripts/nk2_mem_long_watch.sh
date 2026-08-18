#!/bin/bash
# NK2 长时内存验证采样 (2026-08-18): 监控 collect_bc 采集局 + 其 vcmiserver 子进程
# 每 30s 采样 RSS/VSZ, 输出到 /tmp/nk2_mem_long.log, 跑 120 次 = 60 分钟
LOG=/tmp/nk2_mem_long.log
echo "=== NK2 长时内存观测 $(date +%H:%M:%S) ===" > $LOG
for i in $(seq 1 120); do
  TS=$(date +%H:%M:%S)
  # collect 单局子进程 (embedded VCMI: NK2+server 都在此进程内, 无独立 vcmiserver 子进程)
  # 精确锚定 --episode N: 防 --episode 前缀匹配 --episodes (wrapper 主进程), 防 bash wrapper (3MB)
  CPID=$(pgrep -f 'python3 .*collect_bc.py .*--episode [0-9]' | head -1)
  if [ -n "$CPID" ]; then
    CRSS=$(ps -o rss= -p $CPID 2>/dev/null | tr -d ' ')
    CRSS_MB=$((CRSS/1024))
    # 采集进度
    PAIRS=$(grep -c 'pairs' /mnt/d/Bigdata/hero3_fresh/bc_data/nk2_mem_test.log 2>/dev/null)
    DAY=$(grep -oE 'day=[0-9]+' /mnt/d/Bigdata/hero3_fresh/bc_data/nk2_mem_test.log 2>/dev/null | tail -1)
    echo "$TS collect_rss=${CRSS_MB}MB pairs_lines=$PAIRS $DAY" >> $LOG
  else
    echo "$TS collect_proc_gone" >> $LOG
  fi
  sleep 30
done
echo "=== 观测完成 $(date +%H:%M:%S) ===" >> $LOG
echo "DONE"
