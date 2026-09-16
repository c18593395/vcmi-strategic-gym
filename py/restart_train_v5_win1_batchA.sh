#!/bin/bash
# WIN-1 批次A 开窗启动脚本 (09-16) — 击杀激励重设计 P-H1 蓝英雄接近梯度
# 方案: docs/方案_WIN1_击杀激励重设计_20260916.md
# 与 restart_train_v5_sys.sh 唯一差异: unit 注入两条 Environment → 主进程透传 ep_runner:
#   HOMM3_BLUE_HERO_GRAD=0.2      → --blue_hero_grad 0.2      (新低制接近梯度, 空/0=关)
#   HOMM3_BLUE_HERO_GRAD_CAP=25   → --blue_hero_grad_cap 25   (每局累计上限, 0=不限)
# 生效确认: 主日志 grep '[WIN1_BATCH]' (启动一次性) / ep 明细 grep '[BHERO_GRAD]' (逐局)
# 判据(~40局): 蓝英雄最小距离 p50 从 ~128 降至 <64; avg_r 跌幅 <20%; ②④⑤ 不塌
# 回退线: 判据塌 → 跑原版回退: sudo bash /mnt/d/Bigdata/hero3_fresh/py/restart_train_v5_sys.sh
# 批次B 预留 (达标后改本文件 Environment 值即可): HOMM3_BLUE_HERO_CONTACT_R=15 / HOMM3_KILL_R_FIRST=40 / HOMM3_KILL_R_NEXT=30
# 用法: sudo bash /mnt/d/Bigdata/hero3_fresh/py/restart_train_v5_win1_batchA.sh [start|stop|status|log]
set -e
cd /mnt/d/Bigdata/hero3_fresh

cat > /etc/systemd/system/homm3-train-v5.service <<'EOF'
[Unit]
Description=HoMM3 WSL2 PPO v5 training (persistent, system-level)

[Service]
Type=simple
User=administrator
WorkingDirectory=/mnt/d/Bigdata/hero3_fresh
ExecStart=/home/administrator/vcmi-workspace/venv/bin/python train_wsl2_ppo_v2.py
StandardOutput=append:/mnt/d/Bigdata/hero3_fresh/train_loop.log
StandardError=append:/mnt/d/Bigdata/hero3_fresh/train_loop.log
Environment=PATH=/home/administrator/vcmi-workspace/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=HOMM3_BLUE_HERO_GRAD=0.2
Environment=HOMM3_BLUE_HERO_GRAD_CAP=25

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
