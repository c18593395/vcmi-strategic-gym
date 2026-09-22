#!/bin/bash
set -u
pkill -f 'traj_298' 2>/dev/null
sleep 1
echo "=== 探针残留 ==="
ps -ef | grep traj_298 | grep -v grep || echo "已清"
echo ""
echo "=== 训练健康 (主日志尾 3 行) ==="
tail -3 /mnt/d/Bigdata/hero3_fresh/train_loop.log
echo ""
echo "=== ML-wait 日志源定位 ==="
grep -rn "ML-wait" /home/administrator/vcmi-workspace/vcmi_gym/ /home/administrator/vcmi-native/server/ML/ /home/administrator/vcmi-native/client/ 2>/dev/null | grep -v Binary | head -5
