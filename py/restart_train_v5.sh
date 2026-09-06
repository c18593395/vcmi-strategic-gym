#!/bin/bash
# v5 训练重启 (transient unit 停止即消失, 必须 systemd-run 重建; venv 用绝对路径 — hero3_fresh 下无 venv)
cd /mnt/d/Bigdata/hero3_fresh
systemd-run --user --collect --unit=homm3-train-v5 \
  --working-directory=/mnt/d/Bigdata/hero3_fresh \
  /bin/bash -c 'exec /home/administrator/vcmi-workspace/venv/bin/python train_wsl2_ppo_v2.py >> train_loop.log 2>&1'
sleep 5
systemctl --user is-active homm3-train-v5
