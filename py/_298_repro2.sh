#!/bin/bash
# #298 精简复测: judgement/elbow 各1局 + viking 对照1局 (09-23)
set -u
OUT=/tmp/_298_evidence
mkdir -p $OUT
PY="${PY:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER="${RUNNER:-/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py}"
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
SUMMARY=$OUT/summary.txt
CL="${CL:-/home/administrator/vcmi-native/data/VCMI_Client_log.txt}"

run_one() {
  MAP=$1
  TS=$(date +%H%M%S)
  TAG="${MAP%.vmap}_r1_${TS}"
  ELOG=$OUT/ep_${TAG}.log
  echo "=== [$MAP] $(date +%T) start ==="
  timeout 400 $PY $RUNNER 30 /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $ELOG 2>&1
  RC=$?
  STEPS=$(grep -aoE 'steps=[0-9]+' $ELOG | head -1); STEPS=${STEPS#steps=}
  SECS=$(grep -aoE 'secs=[0-9]+' $ELOG | head -1); SECS=${SECS#secs=}
  Q1=$(grep -ac 'Cannot answer the query -1' $CL 2>/dev/null || echo 0)
  FISHY=$(grep -ac 'fishy' $CL 2>/dev/null || echo 0)
  MLQ=$(grep -ac 'popIfTop FAIL' $ELOG 2>/dev/null || echo 0)
  HSE=$(grep -ac 'HEROSEG_EMPTY' $ELOG 2>/dev/null || echo 0)
  TO=$(grep -ac 'adventure_wait timed out' $ELOG 2>/dev/null || echo 0)
  echo "$MAP,1,$RC,${STEPS:-NA},${SECS:-NA},$Q1,$FISHY,$MLQ,$HSE,$TO" >> $SUMMARY
  cp $CL $OUT/vcmi_client_${TAG}.log 2>/dev/null
  echo "    rc=$RC steps=${STEPS:-NA} secs=${SECS:-NA} q-1=$Q1 fishy=$FISHY popFAIL=$MLQ heroseg_empty=$HSE timeout=$TO"
}

echo "map,run,rc,steps,secs,query_neg1,fishy,popIfTopFAIL,hero_seg_empty,timeout300" >> $SUMMARY
run_one judgement_day_h3m.vmap
run_one elbow_room_h3m.vmap
run_one a_viking_we_shall_go_h3m.vmap
echo ""
echo "=== 汇总 (含 good_to_go 前两局) ==="
cat $SUMMARY
