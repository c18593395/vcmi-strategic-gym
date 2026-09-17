#!/bin/bash
# WIN-1 批次B 开窗 + A3 衰减同窗启动脚本 (09-17 备料→09-17 部署) — P-H2 接战 + P-H3 击杀阶梯 + own_town 衰减
# 方案: docs/方案_WIN1_击杀激励重设计_20260916.md §4; A2 定谳+A4 深查: docs/已完成任务.md 09-17 条
# 与 restart_train_v5_win1_batchA.sh 差异: unit Environment 增至 8 条:
#   HOMM3_BLUE_HERO_GRAD=0.2        → --blue_hero_grad 0.2        (P-H1 接近梯度, 批次A 已验证保留)
#   HOMM3_BLUE_HERO_GRAD_CAP=25     → --blue_hero_grad_cap 25     (P-H1 每局上限)
#   HOMM3_BLUE_HERO_CONTACT_R=15    → --blue_hero_contact_r 15    (P-H2 接战奖, 每局每敌 id 一次)
#   HOMM3_BLUE_HERO_CONTACT_D=2     → --blue_hero_contact_d 2     (P-H2 判定距离: 曼哈顿<=2 = 同格+8邻;
#                                                                  ★批次B 必须注入 — 默认 0=仅同格 d==0 而
#                                                                  同格结构性不可达 (#143 事实3/A2 定谳))
#   HOMM3_KILL_R_FIRST=40           → --kill_r_first 40           (P-H3 首杀, 双帧确认)
#   HOMM3_KILL_R_NEXT=30            → --kill_r_next 30            (P-H3 后续杀; 与全歼 proxy +100 同帧叠加)
#   HOMM3_OWN_TOWN_DECAY=0.5        → --own_town_decay 0.5        (A3 own_town 访问衰减 35×0.5^n 封底3次,
#                                                                  治 89.5 霸屏回城循环 — T05 全负唯一根因)
#   HOMM3_OWN_TOWN_MAX_VISITS=4     → --own_town_max_visits 4     (A3 访问硬上限备用闸门)
# 用户拍板 (09-17): 批次B 与 A3 同窗 — 判据可分: 批次B 看 BHERO_CONTACT/BHERO_KILL 事件,
#                  A3 看 [SCORE] own_town 行数/[TOWN_EMPTY]/TOWN_VISIT 次数; T05 r 回升主要归 A3
# 生效确认: 主日志 grep '[WIN1_BATCH]' (应见 8 组注入) / ep 明细 grep '[BHERO_CONTACT]' '[BHERO_KILL]' '[TOWN_EMPTY]'
# 判据(~40局, 方案 §4 + A3 §4): ① 接战率>0 ② 单杀事件非零 ③ TOWN_CAPTURE 真实非零 ④ avg_r 上限 +150 防通胀
#                              A3: own_town pick 行数骤降 (<100/局基线 589) / TOWN_VISIT 降至 ~1-2 次/局
# 回退线: 批次B 塌 → 改回 batchA 脚本; A3 通胀 → 删 HOMM3_OWN_TOWN_DECAY/MAX_VISITS 两行 (独立可撤)
# 部署: sudo bash /mnt/d/Bigdata/hero3_fresh/py/restart_train_v5_win1_batchB.sh start
# 回退: sudo bash /mnt/d/Bigdata/hero3_fresh/py/restart_train_v5_win1_batchA.sh  (仅 P-H1)
#       sudo bash /mnt/d/Bigdata/hero3_fresh/py/restart_train_v5_sys.sh          (全关)
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
Environment=HOMM3_BLUE_HERO_CONTACT_R=15
Environment=HOMM3_BLUE_HERO_CONTACT_D=2
Environment=HOMM3_KILL_R_FIRST=40
Environment=HOMM3_KILL_R_NEXT=30
Environment=HOMM3_OWN_TOWN_DECAY=0.5
Environment=HOMM3_OWN_TOWN_MAX_VISITS=4

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

case "${1:-start}" in
  start)
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
