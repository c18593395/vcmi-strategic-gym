#!/bin/bash
# 冻结/崩溃双模式自动取证 (09-24 v2)
#  - 冻结(124): 有意义引擎行停滞 >20s -> sudo gdb attach 抓全线程栈 -> kill
#  - 崩溃(139): ulimit -c unlimited + core_pattern=/tmp/ -> gdb 尸检 core
# 用法: wsl bash /mnt/d/Bigdata/hero3_fresh/py/_298_freeze_capture.sh [n_runs] [turns]
set -u
N=${1:-8}
TURNS=${2:-30}
MAP=elbow_room_h3m.vmap
OUT=/tmp/_298_evidence/capture2
COREDIR=/tmp/cores
mkdir -p $OUT $COREDIR

# core dump 配置(仅本次 WSL boot 有效)
echo "/tmp/cores/core.%p" > /proc/sys/kernel/core_pattern 2>/dev/null || sudo -n sh -c 'echo "/tmp/cores/core.%p" > /proc/sys/kernel/core_pattern'

PY="${PY:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER="${RUNNER:-/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py}"

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

TS=$(date +%H%M%S)
echo "=== capture2 x$N turns=$TURNS start $(date +%T) so=$(md5sum /home/administrator/vcmi-native/rel/bin/libmlclient.so | cut -c1-12) ==="

for i in $(seq 1 $N); do
  LOG=$OUT/cap2_${TS}_r$i.log
  ( ulimit -c unlimited; exec timeout 300 $PY $RUNNER $TURNS /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 ) > $LOG 2>&1 &
  PROCPID=$!
  CAPTURED=0
  LASTMEAN=0
  STALL=0
  for w in $(seq 1 70); do
    sleep 4
    kill -0 $PROCPID 2>/dev/null || break
    MEAN=$(grep -anE 'ML-stk|ML-obj|ML-q|EP_TIME|runServer|ML-battle' $LOG 2>/dev/null | tail -n 1 | cut -d: -f1)
    MEAN=${MEAN:-0}
    if [ "$MEAN" -eq "$LASTMEAN" ]; then
      STALL=$((STALL + 4))
    else
      STALL=0
      LASTMEAN=$MEAN
    fi
    if [ $STALL -ge 20 ] && [ $CAPTURED -eq 0 ]; then
      STACK=$OUT/cap2_${TS}_r${i}_stacks.txt
      PYPID=$(pgrep -P $PROCPID -f 'python' | head -n 1)
      PYPID=${PYPID:-$PROCPID}
      echo "--- r$i 冻结(有意义行停滞 ${STALL}s, line=$MEAN), gdb attach pid=$PYPID (timeout=$PROCPID) ---"
      sudo -n gdb -p $PYPID -batch -nx \
        -ex 'set pagination off' \
        -ex 'echo \n===== FREEZE SNAPSHOT =====\n' \
        -ex 'thread apply all bt 20' \
        > $STACK 2>&1
      CAPTURED=1
      echo "--- r$i 栈已存 $STACK (线程 $(grep -c 'Thread ' $STACK)) ---"
      break
    fi
  done
  if kill -0 $PROCPID 2>/dev/null; then
    kill -9 $PROCPID 2>/dev/null
  fi
  wait $PROCPID 2>/dev/null
  RC=$?
  EP=$(grep -ac EP_TIME $LOG)
  EX=$(grep -ac 'runServer EXIT' $LOG)
  NOTE=""
  if [ $RC -eq 139 ] || [ $RC -eq 134 ]; then
    CORE=$(ls -t $COREDIR/core.* 2>/dev/null | head -n 1)
    [ -n "${CORE:-}" ] && NOTE="core=$CORE"
  fi
  [ $CAPTURED -eq 1 ] && NOTE="$NOTE stacks=YES"
  echo "r$i rc=$RC EP_TIME=$EP EXIT=$EX $NOTE log=$LOG"
done
echo "=== done $(date +%T) ==="