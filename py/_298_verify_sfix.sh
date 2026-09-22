#!/bin/bash
# #298 S 修复验证: 4 图各 1 局 (30 步), 修复后应 rc=0 steps=30 secs 正常 (09-23)
set -u
OUT=/tmp/_298_evidence
mkdir -p $OUT
PY=/home/administrator/vcmi-workspace/venv/bin/python
RUNNER=/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
SUMMARY=$OUT/verify_s_fix.txt
CL=/home/administrator/vcmi-native/data/VCMI_Client_log.txt
: > $SUMMARY
echo "map,rc,steps,secs,swallow,timeout300" >> $SUMMARY

for MAP in good_to_go_h3m.vmap judgement_day_h3m.vmap elbow_room_h3m.vmap a_viking_we_shall_go_h3m.vmap; do
  TS=$(date +%H%M%S)
  TAG="${MAP%.vmap}_sfix_${TS}"
  ELOG=$OUT/ep_${TAG}.log
  echo "=== [$MAP] $(date +%T) start ==="
  timeout 300 $PY $RUNNER 30 /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $ELOG 2>&1
  RC=$?
  STEPS=$(grep -aoE 'steps=[0-9]+' $ELOG | head -1); STEPS=${STEPS#steps=}
  SECS=$(grep -aoE 'secs=[0-9]+' $ELOG | head -1); SECS=${SECS#secs=}
  SW=$(grep -ac 'EP298_SWALLOW' $ELOG 2>/dev/null || echo 0)
  TO=$(grep -ac 'adventure_wait timed out' $ELOG 2>/dev/null || echo 0)
  echo "$MAP,$RC,${STEPS:-NA},${SECS:-NA},$SW,$TO" >> $SUMMARY
  echo "    rc=$RC steps=${STEPS:-NA} secs=${SECS:-NA} swallow=$SW timeout=$TO"
done
echo ""
echo "=== 验证汇总 (判据: 全部 rc=0 steps=30 secs<200 swallow=0 timeout=0) ==="
column -t -s, $SUMMARY 2>/dev/null || cat $SUMMARY
