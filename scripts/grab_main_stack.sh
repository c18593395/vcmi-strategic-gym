#!/bin/bash
# 抓主线程 + NK2 线程完整栈 (过滤 warning)
cd /home/administrator/vcmi-workspace
su administrator -c '/home/administrator/vcmi-workspace/venv/bin/python -u /mnt/d/Bigdata/hero3_fresh/scripts/diag_repro.py > /tmp/diag_run8.log 2>&1 &'
for i in $(seq 1 40); do
  sleep 5
  if grep -aq "step1" /tmp/diag_run8.log; then break; fi
done
P=$(pgrep -f diag_repro | head -1)
echo "pid=$P"
gdb -p "$P" -batch -ex "set pagination off" -ex "thread 1" -ex "bt 30" -ex "thread 14" -ex "bt 30" 2>&1 | grep -vE "warning:|New LWP|^\[" | head -80
