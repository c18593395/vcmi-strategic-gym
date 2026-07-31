#!/bin/bash
# BC 采集 watchdog: 每 20 分钟检查一次, 采集完成或异常时退出并汇报
LOG=/mnt/d/Bigdata/hero3_fresh/bc_data/bc_v2/collect.log
OUT=/mnt/d/Bigdata/hero3_fresh/bc_data/bc_v2
while true; do
  sleep 1200   # 20 分钟
  if wsl bash -c 'pgrep -f "collect_bc.py --episodes" >/dev/null 2>&1'; then
    echo "--- $(date +%H:%M) 采集中 ---"
    wsl bash -c "tail -3 $LOG 2>/dev/null; echo -n 'ep 文件数: '; ls -1 $OUT/bc_raw_ep*.npz 2>/dev/null | wc -l"
  else
    if wsl bash -c 'echo ok' >/dev/null 2>&1; then
      echo "=== 采集进程已退出 ==="
      wsl bash -c "tail -5 $LOG 2>/dev/null; echo ---; ls -lt $OUT/bc_raw_ep*.npz 2>/dev/null; echo ---; python3 -c \"import glob,numpy as np; tot=sum(len(np.load(f)['obs']) for f in glob.glob('$OUT/bc_raw_ep*.npz')); print('TOTAL pairs:', tot)\" 2>/dev/null || echo 'pairs 统计失败'"
      exit 0
    else
      echo "!!! $(date +%H:%M) WSL 无响应(可能重启), 采集进程丢失, 需人工检查"
      exit 1
    fi
  fi
done
