#!/usr/bin/env bash
# OPS-20260828-01 续训 v3：setsid + nohup 真后台。返回最终存活的 python PID + chain PID
set -e
cd /mnt/d/Bigdata/hero3_fresh

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
export PYTHONPATH=/mnt/d/Bigdata/hero3_fresh

# 分隔线
echo "" >> train_loop.log
echo "===== OPS-20260828-01 RESUME v3 @ $(date '+%Y-%m-%d %H:%M:%S') | expect step=153785+ =====" >> train_loop.log

# 清理可能残留 (保险)
set +e
pkill -f 'train_wsl2_ppo_v2.py' 2>/dev/null
pkill -f 'ep_runner_one.py'   2>/dev/null
sleep 1
set -e

# 用 setsid 让整管道脱离当前会话；重定向 nohup.out
SETSID_OUTFILE="/mnt/d/Bigdata/hero3_fresh/py/nohup_train_setsid.log"
: > "$SETSID_OUTFILE"

setsid bash -c '
  cd /mnt/d/Bigdata/hero3_fresh
  export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
  export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
  export PYTHONPATH=/mnt/d/Bigdata/hero3_fresh
  exec nohup /home/administrator/vcmi-workspace/venv/bin/python3 -u train_wsl2_ppo_v2.py 2>&1 \
    | tee -a train_loop.log >>/dev/null
' >/dev/null 2>&1 < /dev/null &
SETSID_BG=$!
echo "SETSID_BG=$SETSID_BG"
disown || true

sleep 4
echo '=== ps check ==='
ps -efH | grep -E 'train_wsl2_ppo_v2|ep_runner_one|tee -a train_loop' | grep -v grep || true
PY_PID=$(ps -ef | grep 'train_wsl2_ppo_v2.py' | grep -v grep | awk 'NR==1{print $2}')
echo "PY_PID=$PY_PID"

echo '=== tail from resume v3 marker, last 30 ==='
awk '/^===== OPS-20260828-01 RESUME v3/,0' /mnt/d/Bigdata/hero3_fresh/train_loop.log | tail -30
