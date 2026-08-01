#!/bin/bash
# 抓 diag_repro 卡死时 NK2/VCMI 关键线程栈
cd /home/administrator/vcmi-workspace
su administrator -c '/home/administrator/vcmi-workspace/venv/bin/python -u /mnt/d/Bigdata/hero3_fresh/scripts/diag_repro.py > /tmp/diag_run6.log 2>&1 &'
for i in $(seq 1 40); do
  sleep 5
  if grep -aq "step1" /tmp/diag_run6.log; then
    echo "step1 卡死窗口 @ $((i*5))s"
    break
  fi
done
P=$(pgrep -f diag_repro | head -1)
echo "pid=$P"
gdb -p "$P" -batch -ex "thread apply all bt 10" 2>&1 | grep -B2 -A12 "makingTurn\|AIGateway\|Nullkiller\|CGameHandler\|startBattle\|AAI\|yourTurn\|runNetwork\|CClient\|battle\|moveHero" | head -100
