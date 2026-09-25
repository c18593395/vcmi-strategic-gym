#!/bin/bash
# #298 看门狗冒烟: judgement 单局 (boot hang 概率性, 跑通=不误杀; hang=看门狗 400s 实战)
set -u
OUT=/tmp/_298_evidence
PY="${PY:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER="${RUNNER:-/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py}"
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
TS=$(date +%H%M%S)
ELOG=$OUT/ep_judgement_wd_${TS}.log
echo "=== judgement 看门狗冒烟 $(date +%T) (timeout 550 上限保险) ==="
timeout 550 $PY $RUNNER 30 /tmp/traj_298.json judgement_day_h3m.vmap --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $ELOG 2>&1
RC=$?
echo "rc=$RC"
echo "WD_KILL: $(grep -ac 'WD_KILL' $ELOG)"
echo "SWALLOW: $(grep -ac 'EP298_SWALLOW' $ELOG)"
echo "EP_TIME: $(grep -a 'EP_TIME' $ELOG | head -1)"
echo "lines: $(wc -l < $ELOG)"
echo "尾 3 行:"
tail -3 $ELOG | cut -c1-150
