#!/bin/bash
# 复现 09-24 池图开局故障 + 抓冻结/卡死现场
# 现象: 3 局池图 hit=True 后全 [WARN] traj 读取失败 (rc=0, 无 [EP_TIME])
# 假设: 池图开局 reset 失败/卡死 → 子进程首步写 traj 前退出
set -u
VENV=/home/administrator/vcmi-workspace/venv/bin/python
RUNNER=/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py
B=/home/administrator/vcmi-native
OUT=/tmp/_296_repro
mkdir -p $OUT
export LD_LIBRARY_PATH=$B/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=$B/rel/bin/libmlclient.so

for MAP in good_to_go_h3m.vmap judgement_day_h3m.vmap; do
  TS=$(date +%H%M%S)
  LOG=$OUT/ep_${MAP%.vmap}_${TS}.log
  echo "=== 复现 [$MAP] $(date +%T) ==="
  # 30 步、60s 超时（池图正常 30 步 ~30s，卡死则 60s 超时）
  timeout 60 $VENV $RUNNER 30 $OUT/traj.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $LOG 2>&1
  RC=$?
  STEPS=$(grep -aoE 'steps=[0-9]+' $LOG | head -1); STEPS=${STEPS#steps=}
  SECS=$(grep -aoE 'secs=[0-9]+' $LOG | head -1); SECS=${SECS#secs=}
  SW=$(grep -ac 'EP298_SWALLOW' $LOG 2>/dev/null || echo 0)
  TO=$(grep -ac 'adventure_wait timed out' $LOG 2>/dev/null || echo 0)
  BRK=$(grep -ac 'ML-upg.*BREAK' $LOG 2>/dev/null || echo 0)
  echo "  rc=$RC steps=${STEPS:-NA} secs=${SECS:-NA} swallow=$SW timeout=$TO break=$BRK"
  echo "  --- 日志头 8 行 ---"
  head -8 $LOG | cut -c1-120
  echo "  --- 日志尾 8 行 ---"
  tail -8 $LOG | cut -c1-120
  echo "  --- 关键标记 ---"
  grep -aE 'query -1|Cannot answer|force game_over|EP_TIME|START_HOME|traj|reset|ERROR|FAIL' $LOG | head -15 | cut -c1-130
  echo
done
echo "=== 复现完成 $(date +%T) ==="
ls -la $OUT
