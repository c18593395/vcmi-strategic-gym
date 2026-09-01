#!/usr/bin/env bash
# OPS-20260828-01 续训 Run9 下一段: 后台启动 + tee -a 追加 train_loop.log
set -e
cd /mnt/d/Bigdata/hero3_fresh

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
export PYTHONPATH=/mnt/d/Bigdata/hero3_fresh

# 追加日志分隔符 (UTC+8 本机时间)
echo "" >> train_loop.log
echo "===== OPS-20260828-01 RESUME @ $(date '+%Y-%m-%d %H:%M:%S') | expect step=153785+ =====" >> train_loop.log

# 后台启动: nohup ... | tee -a train_loop.log >/dev/null &
nohup /home/administrator/vcmi-workspace/venv/bin/python3 -u train_wsl2_ppo_v2.py 2>&1 \
  | tee -a train_loop.log >/dev/null &
CHAIN_PID=$!
# 拿到 tee 的 PID，但其父进程是 bash；真正的 python PID 在下面 ps 中核对
echo "CHAIN_PID=$CHAIN_PID"
sleep 2
echo "=== ps -ef | grep train_wsl2_ppo_v2 ==="
ps -ef | grep train_wsl2_ppo_v2 | grep -v grep
echo "=== last 25 lines of log (new lines only, tail after resume marker) ==="
awk '/^===== OPS-20260828-01 RESUME/,0' train_loop.log | tail -25
