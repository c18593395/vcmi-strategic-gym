#!/bin/bash
# #298 慢 vs 卡定性: good_to_go/judgement 各 1 局 timeout 600 (09-23)
set -u
OUT=/tmp/_298_evidence
PY=/home/administrator/vcmi-workspace/venv/bin/python
RUNNER=/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
SUMMARY=$OUT/verify_s600.txt
: > $SUMMARY
echo "map,rc,steps,secs,swallow,err" >> $SUMMARY

for MAP in good_to_go_h3m.vmap judgement_day_h3m.vmap; do
  TS=$(date +%H%M%S)
  TAG="${MAP%.vmap}_s600_${TS}"
  ELOG=$OUT/ep_${TAG}.log
  echo "=== [$MAP] $(date +%T) start (timeout 600) ==="
  timeout 600 $PY $RUNNER 30 /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $ELOG 2>&1
  RC=$?
  STEPS=$(grep -aoE 'steps=[0-9]+' $ELOG | head -1); STEPS=${STEPS#steps=}
  SECS=$(grep -aoE 'secs=[0-9]+' $ELOG | head -1); SECS=${SECS#secs=}
  SW=$(grep -ac 'EP298_SWALLOW' $ELOG 2>/dev/null || echo 0)
  ER=$(grep -aoE 'err=[a-z]+' $ELOG | head -1); ER=${ER#err=}
  echo "$MAP,$RC,${STEPS:-NA},${SECS:-NA},$SW,${ER:-NA}" >> $SUMMARY
  echo "    rc=$RC steps=${STEPS:-NA} secs=${SECS:-NA} swallow=$SW err=${ER:-NA}"
done
echo ""
column -t -s, $SUMMARY 2>/dev/null || cat $SUMMARY
