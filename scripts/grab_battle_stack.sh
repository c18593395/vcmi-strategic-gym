#!/bin/bash
# 战斗卡死现场抓取 (root 运行)
cd /home/administrator/vcmi-workspace
su administrator -c '/home/administrator/vcmi-workspace/venv/bin/python -u /mnt/d/Bigdata/hero3_fresh/scripts/diag_repro.py > /tmp/diag_b3.log 2>&1 &'
for i in $(seq 1 40); do
  sleep 5
  grep -aq "battleStarted" /tmp/diag_b3.log && break
done
echo "战斗已开始, 等 30s 进入卡死窗口"
sleep 30
P=$(pgrep -f diag_repro | head -1)
echo "pid=$P"
gdb -p "$P" -batch -ex "set pagination off" -ex "thread apply all bt 10" 2>&1 > /tmp/gdb_b3.txt
grep -E "^Thread [0-9]+ \(Thread" -A 10 /tmp/gdb_b3.txt | grep -B1 -A9 -iE "NK2|Nullkiller|CGameHandler|BattleProcessor|AAI|AIGateway|waitTillFree|runNetwork|CClient|CAdventureAI|moveHero" | grep -vE "blas_thread|openblas|numpy" | head -70
rm -f /tmp/gdb_b3.txt
