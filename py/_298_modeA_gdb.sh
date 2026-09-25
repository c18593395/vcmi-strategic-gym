#!/bin/bash
# Mode A (runServer EXIT) 元凶抓捕 (09-24): gdb 断点 setState(SHUTDOWN) / NetworkHandler::stop
# 命中即打调用者全栈 + 全线程栈, kill 本局, 继续下一局直到抓到或跑满 N 局
# 用法: wsl bash /mnt/d/Bigdata/hero3_fresh/py/_298_modeA_gdb.sh [n_runs] [turns]
set -u
N=${1:-8}
TURNS=${2:-30}
MAP=elbow_room_h3m.vmap
OUT=/tmp/_298_evidence/modeA
mkdir -p $OUT
PY="${PY:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER="${RUNNER:-/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py}"

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

TS=$(date +%H%M%S)
echo "=== modeA-hunt x$N turns=$TURNS start $(date +%T) ==="

for i in $(seq 1 $N); do
  LOG=$OUT/mA_${TS}_r$i.log
  STACK=$OUT/mA_${TS}_r${i}_killer.txt
  timeout 360 gdb -batch -nx \
    -ex 'set pagination off' \
    -ex 'set confirm off' \
    -ex 'break CVCMIServer::setState if value == 2' \
    -ex 'break NetworkHandler::stop' \
    -ex 'commands 1 2
silent
printf "\n===== KILLER HIT bp%d =====\n", $bpnum
bt 30
echo \n----- ALL THREADS -----\n
thread apply all bt 12
kill
quit
end' \
    -ex "run > $LOG 2>&1" \
    --args $PY $RUNNER $TURNS /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 \
    > $STACK 2>&1
  RC=$?
  HIT=$(grep -c 'KILLER HIT' $STACK 2>/dev/null)
  echo "r$i rc=$RC killer_hit=$HIT stack=$STACK log=$LOG"
  if [ "$HIT" != "0" ]; then
    echo "=== 抓到元凶, 提前结束 ==="
    grep -A34 'KILLER HIT' $STACK | head -45
    break
  fi
done
echo "=== done $(date +%T) ==="