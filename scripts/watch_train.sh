#!/bin/bash
# 训练 watchdog: 每 20 分钟输出 TRAIN_CHECK 行 (进度或异常), 训练进程消失时退出
# 注意: train_loop.sh tee 到 train_loop.log (新训练); c85.log 为兼容旧名
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
prev=""
while true; do
  sleep 1200   # 20 分钟
  ts=$(date +%H:%M)
  if wsl bash -c 'pgrep -f "train_loop.sh" >/dev/null 2>&1 || pgrep -f "train_wsl2_ppo_v2.py" >/dev/null 2>&1'; then
    cur=$(wsl bash -c "grep -aE 'step +[0-9]+' $LOG 2>/dev/null | tail -1")
    if [ -z "$cur" ]; then
      echo "TRAIN_CHECK $ts: 训练进程在但日志无 step 输出 (可能卡在启动/加载)"
      wsl bash -c "tail -3 $LOG 2>/dev/null"
    elif [ "$cur" != "$prev" ]; then
      echo "TRAIN_CHECK $ts: $cur"
      prev="$cur"
    else
      echo "TRAIN_CHECK $ts: (进度未变) $cur"
    fi
  else
    echo "TRAIN_CHECK $ts: !!! 训练进程消失, 日志尾部:"
    wsl bash -c "tail -15 $LOG 2>/dev/null"
    exit 1
  fi
done
