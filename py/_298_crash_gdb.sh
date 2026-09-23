#!/bin/bash
# 崩溃栈取证 (09-23): 以 gdb 前台运行 ep_runner, 命中 SIGSEGV 自动打印故障线程+全线程栈
# 用法: wsl bash /mnt/d/Bigdata/hero3_fresh/py/_298_crash_gdb.sh [map] [turns]
set -u
MAP=${1:-elbow_room_h3m.vmap}
TURNS=${2:-30}
OUT=/tmp/_298_evidence
mkdir -p $OUT
TS=$(date +%H%M%S)
STACK=$OUT/crash_stack_${MAP%.vmap}_${TS}.txt
INFLOG=$OUT/crash_inferior_${MAP%.vmap}_${TS}.log
PY=/home/administrator/vcmi-workspace/venv/bin/python
RUNNER=/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

echo "=== [crash-gdb] $MAP turns=$TURNS start $(date +%T) ==="
timeout 420 gdb -batch -nx \
  -ex 'set pagination off' \
  -ex 'set confirm off' \
  -ex 'handle SIGSEGV stop print nopass' \
  -ex "run > $INFLOG 2>&1" \
  -ex 'echo \n##### FAULTING THREAD #####\n' \
  -ex 'bt 45' \
  -ex 'echo \n##### REGISTERS #####\n' \
  -ex 'info registers rip rsp' \
  -ex 'echo \n##### ALL THREADS (bt 12) #####\n' \
  -ex 'thread apply all bt 12' \
  --args $PY $RUNNER $TURNS /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 \
  > $STACK 2>&1

echo "rc=$?"
echo "--- inferior 日志尾 ---"
tail -n 8 $INFLOG 2>/dev/null | cut -c1-160
echo ""
echo "--- 崩溃栈 (前 70 行) ---"
head -70 $STACK
echo ""
echo "文件: $STACK / $INFLOG"