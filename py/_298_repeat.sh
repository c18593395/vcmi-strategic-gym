#!/bin/bash
# 重复跑同一张图 N 局, 统计 rc 分布 (用于竞态类问题的复现率/A-B 对照)
# 用法: wsl bash /mnt/d/Bigdata/hero3_fresh/py/_298_repeat.sh [map] [n] [turns]
set -u
MAP=${1:-elbow_room_h3m.vmap}
N=${2:-6}
TURNS=${3:-30}
OUT=/tmp/_298_evidence/repeat
mkdir -p $OUT
TS=$(date +%H%M%S)
PY="${PY:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER="${RUNNER:-/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py}"

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

echo "=== repeat $MAP x$N turns=$TURNS start $(date +%T) (so_md5=$(md5sum /home/administrator/vcmi-native/rel/bin/libmlclient.so | cut -c1-12)) ==="
for i in $(seq 1 $N); do
  LOG=$OUT/${MAP%.vmap}_${TS}_r$i.log
  timeout 300 $PY $RUNNER $TURNS /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $LOG 2>&1
  RC=$?
  ST=$(grep -aoE 'steps=[0-9]+' $LOG | head -1)
  SC=$(grep -aoE 'secs=[0-9]+' $LOG | head -1)
  echo "  run$i rc=$RC ${ST:-no-steps} ${SC:-no-secs} log=$LOG"
done
echo "=== done $(date +%T) ==="