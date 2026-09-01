#!/usr/bin/env bash
# OPS-20260828-01 续训启动 v2：使用 setsid + nohup 双重守护化，先交互式跑 12s 看失败堆栈
set +e
cd /mnt/d/Bigdata/hero3_fresh

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
export PYTHONPATH=/mnt/d/Bigdata/hero3_fresh

# 交互式短跑：捕获首屏错误
TIMEOUT=14
echo "=== run $TIMEOUT seconds interactively to catch init errors ==="
timeout --kill-after=2 --signal=TERM $TIMEOUT \
  /home/administrator/vcmi-workspace/venv/bin/python3 -u train_wsl2_ppo_v2.py 2>&1 \
  | tee -a train_loop.log | head -80
RC=${PIPESTATUS[0]}
echo "--- interactive rc=$RC ---"
