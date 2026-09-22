#!/bin/bash
# #298: ML-wait 对比 + viking 局结果 + 训练进程状态 (09-23)
set -u
echo "=== good_to_go r1 有无 ML-wait ==="
grep -ac 'ML-wait' /tmp/_298_evidence/ep_good_to_go_h3m_r1_022710.log 2>/dev/null
grep -a 'ML-wait' /tmp/_298_evidence/ep_good_to_go_h3m_r1_022710.log 2>/dev/null | head -5
echo ""
echo "=== judgement 有无 ML-wait ==="
grep -ac 'ML-wait' /tmp/_298_evidence/ep_judgement_day_h3m_r1_024101.log 2>/dev/null
echo ""
echo "=== elbow 有无 ML-wait ==="
grep -ac 'ML-wait' /tmp/_298_evidence/ep_elbow_room_h3m_r1_024615.log 2>/dev/null
echo ""
echo "=== viking 局结果 ==="
h=/tmp/_298_evidence/ep_a_viking_we_shall_go_h3m_r1_025127.log
grep -aE 'EP_TIME|timed out' "$h" | tail -3
echo "ML-wait 计数: $(grep -ac 'ML-wait' "$h")"
echo "ML-wait 去重种类:"
grep -a 'ML-wait' "$h" | sort -u | head -8
echo ""
echo "=== summary 终版 ==="
cat /tmp/_298_evidence/summary.txt
echo ""
echo "=== 训练 unit 状态 (谁拉起的?) ==="
systemctl is-active homm3-train-v5
ps -ef | grep 'train_wsl2_ppo_v2' | grep -v grep | head -2
