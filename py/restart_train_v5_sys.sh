#!/bin/bash
# v5 训练 — machine 级 systemd 持久 unit (随 VM 生命周期, 不受 user 会话退出影响)
# 用法: sudo bash /mnt/d/Bigdata/hero3_fresh/py/restart_train_v5_sys.sh [start|stop|status|log]
set -e
cd /mnt/d/Bigdata/hero3_fresh

# 踩坑 #308 固件: VCMI 在非 root 身份下依赖 $XDG_DATA_HOME/vcmi/data/Maps,
# 缺该目录链会导致 VFS 打开 .vmap 失败 → std::terminate → SIGABRT (池图必崩)。
# 幂等, 需 root (内含 chown)。务必在 start 之前执行。
bash /mnt/d/Bigdata/hero3_fresh/py/setup_vcmi_runtime.sh || true

cat > /etc/systemd/system/homm3-train-v5.service <<'EOF'
[Unit]
Description=HoMM3 WSL2 PPO v5 training (persistent, system-level)

[Service]
Type=simple
User=administrator
WorkingDirectory="${WorkingDirectory:-/mnt/d/Bigdata/hero3_fresh}"
# 踩坑 #308: 显式指定 XDG 数据目录, 勿依赖 threadconnector 的 getenv 默认推导
Environment="${Environment:-XDG_DATA_HOME=/home/administrator/.local/share}"
ExecStart="${ExecStart:-/home/administrator/vcmi-workspace/venv/bin/python py/train_wsl2_ppo_v2.py}"
StandardOutput="${StandardOutput:-append:/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
StandardError="${StandardError:-append:/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
Environment="${Environment:-PATH=/home/administrator/vcmi-workspace/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"

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
