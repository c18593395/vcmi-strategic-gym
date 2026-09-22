#!/bin/bash
set -u
pkill -f 'traj_298' 2>/dev/null
sleep 2
systemctl start homm3-train-v5
sleep 3
echo "unit: $(systemctl is-active homm3-train-v5)"
ps -ef | grep train_wsl2_ppo_v2 | grep -v grep | head -1 || echo "(主进程未起!)"
