#!/bin/bash
# v5 训练 — machine 级 systemd 持久 unit (随 VM 生命周期, 不受 user 会话退出影响)
# 用法: sudo bash /mnt/d/Bigdata/hero3_fresh/py/restart_train_v5_sys.sh [start|stop|status|log]
set -e
cd /mnt/d/Bigdata/hero3_fresh

cat > /etc/systemd/system/homm3-train-v5.service <<'EOF'
[Unit]
Description=HoMM3 WSL2 PPO v5 training (persistent, system-level)

[Service]
Type=simple
User=administrator
WorkingDirectory=/mnt/d/Bigdata/hero3_fresh
ExecStart=/home/administrator/vcmi-workspace/venv/bin/python py/train_wsl2_ppo_v2.py
StandardOutput=append:/mnt/d/Bigdata/hero3_fresh/train_loop.log
StandardError=append:/mnt/d/Bigdata/hero3_fresh/train_loop.log
Environment=PATH=/home/administrator/vcmi-workspace/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

case "${1:-start}" in
  start)
    # stop user-level transient twin if any, to avoid double training
    systemctl --user stop homm3-train-v5.service 2>/dev/null || true
    systemctl restart homm3-train-v5
    sleep 5
    systemctl is-active homm3-train-v5
    ;;
  stop)
    systemctl stop homm3-train-v5
    systemctl is-active homm3-train-v5 || true
    ;;
  status)
    systemctl is-active homm3-train-v5
    ps aux | grep -E 'train_wsl2_ppo_v2|ep_runner' | grep -v grep | head -5
    tail -5 /mnt/d/Bigdata/hero3_fresh/train_loop.log
    ;;
  log)
    tail -30 /mnt/d/Bigdata/hero3_fresh/train_loop.log
    ;;
esac
