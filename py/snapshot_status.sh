#!/usr/bin/env bash
# 单次状态快照: 服务/进程/step 行/最近 ep
svc=homm3-train-v5
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
echo "== snapshot @ $(date) =="
echo "== service =="
systemctl is-active "$svc"
PID=$(systemctl show -p MainPID --value "$svc")
echo "PID=$PID etime=$(ps -o etime= -p "$PID" 2>/dev/null | tr -d ' ')"
echo "== ep processes =="
ps -o pid,etime,cmd -C python 2>/dev/null | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | sed 's/--model.*//'
echo "== last step lines =="
grep -aE '^step[0-9]+' "$LOG" | tail -n 12
echo "== last EP_TIME =="
grep -a 'EP_TIME' "$LOG" | tail -n 3
echo "== log mtime =="
stat -c '%y %s bytes' "$LOG"
