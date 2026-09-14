#!/bin/bash
# ======================================================================
# ⚠️ 已废弃 (2026-09-11): 本脚本重建旧 user 级 transient unit,
#    与现行 system 级 enabled unit (/etc/systemd/system/homm3-train-v5.service)
#    双开会拉起第二个训练进程! 现行运维一律用:
#      wsl -u root systemctl stop|start|restart homm3-train-v5
#    或: sudo bash py/restart_train_v5_sys.sh [start|stop|status]
#    背景见踩坑 #195/#201。保留本文件仅作历史参考, 禁止执行。
# ======================================================================
echo "FATAL: restart_train_v5.sh 已废弃 (user transient); 请用 wsl -u root systemctl ... 或 restart_train_v5_sys.sh" >&2
exit 100

# --- 以下为 09-11 前旧流程, 不会执行到 ---
# v5 训练重启 (transient unit 停止即消失, 必须 systemd-run 重建; venv 用绝对路径 — hero3_fresh 下无 venv)
cd /mnt/d/Bigdata/hero3_fresh
systemd-run --user --collect --unit=homm3-train-v5 \
  --working-directory=/mnt/d/Bigdata/hero3_fresh \
  /bin/bash -c 'exec /home/administrator/vcmi-workspace/venv/bin/python train_wsl2_ppo_v2.py >> train_loop.log 2>&1'
sleep 5
systemctl --user is-active homm3-train-v5
