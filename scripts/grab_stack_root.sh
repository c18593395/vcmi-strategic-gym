#!/bin/bash
# 以 root 抓 diag_repro 卡死线程栈
cd /home/administrator/vcmi-workspace
su administrator -c '/home/administrator/vcmi-workspace/venv/bin/python -u /mnt/d/Bigdata/hero3_fresh/scripts/diag_repro.py > /tmp/diag_run4.log 2>&1 &'
for i in $(seq 1 40); do
  sleep 5
  if grep -aq "step1" /tmp/diag_run4.log; then
    echo "step1 卡死窗口 @ $((i*5))s"
    break
  fi
done
P=$(pgrep -f diag_repro | head -1)
echo "diag pid=$P"
gdb -p "$P" -batch -ex "thread apply all bt 8" 2>&1 | grep -E "^Thread [0-9]|#[0-9] " | head -70
