#!/bin/bash
# 回滚对照单组: bash _rollback_one.sh <TAG> <CKPT路径> (09-21)
set -u
ROOT="${ROOT:-/mnt/d/Bigdata/hero3_fresh}"
VENV="${VENV:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER=$ROOT/py/ep_runner_one.py
export LD_LIBRARY_PATH="/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
export STRATEGIC_STATE_LIB="/home/administrator/vcmi-native/rel/bin/libmlclient.so"
TAG=$1
CK=$2
cd /home/administrator/vcmi-native
for MAP in T06_adventure_72X72_02.vmap T06_adventure_72X72_01.vmap T06_adventure_108X108_02_duel.vmap; do
  T=/tmp/_rc_traj_${TAG}_${MAP}.json
  timeout 420 $VENV $RUNNER 250 $T $MAP --model $CK \
    --blue_ai MMAI_RANDOM --blue_adventure_ai MMAI \
    --reward_explore 0.3 --move_to_bias 1.92 --move_to_force 60 --act_loop_from_step 60 \
    --economy_force 24 --cycle_detect 5 --act_loop_penalty 1.0 --guard_done_steps 15 \
    --objective_reward 30 --target_chain scorer > /tmp/_rc_${TAG}_$MAP.log 2>&1
  LINE=$(grep -aE 'EP_TIME' /tmp/_rc_${TAG}_$MAP.log | tail -1)
  DEAD=$(grep -acE 'RED_DEAD|HERO_DEATH' /tmp/_rc_${TAG}_$MAP.log)
  BLK=$(grep -acE 'SCORE_BLACK' /tmp/_rc_${TAG}_$MAP.log)
  echo "[$TAG] $MAP | $LINE | dead=$DEAD black=$BLK"
done
echo "GROUP-$TAG-DONE"
