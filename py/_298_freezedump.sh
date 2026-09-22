#!/bin/bash
# #298 冻结窗栈取证 (09-23): 字节增长检测冻结 → 冻结窗内抓 /proc 线程态 + gdb 全线程栈
# 原理: 冻结 = 日志字节零增长; 检测到连续 6 次(12s)零增长且 t>15s → 一次性取证
# 用法: wsl -u root bash /mnt/d/Bigdata/hero3_fresh/py/_298_freezedump.sh [map] [turns]
set -u
MAP=${1:-good_to_go_h3m.vmap}
TURNS=${2:-30}
OUT=/tmp/_298_evidence
mkdir -p $OUT
PY=/home/administrator/vcmi-workspace/venv/bin/python
RUNNER=/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py
TS=$(date +%H%M%S)
LOG=$OUT/ep_freeze_${MAP%.vmap}_${TS}.log
PROC=$OUT/freeze_proc_${MAP%.vmap}_${TS}.txt
DUMP=$OUT/freeze_gdb_${MAP%.vmap}_${TS}.txt
SAMP=$OUT/freeze_samples_${MAP%.vmap}_${TS}.csv

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

echo "t,bytes" > $SAMP
echo "=== [freeze-dump] $MAP turns=$TURNS start $(date +%T) ==="
timeout 420 $PY $RUNNER $TURNS /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $LOG 2>&1 &
PID=$!
sleep 2
# $! 是 timeout 进程; 真正跑引擎的是它的子进程 (python/ep_runner, 引擎进程内 server)
CHILD=$(pgrep -P $PID 2>/dev/null | head -1)
[ -z "$CHILD" ] && CHILD=$PID
echo "  timeout_pid=$PID  engine_pid=$CHILD ($(cat /proc/$CHILD/comm 2>/dev/null))"
T0=$(date +%s)
FLAT=0
PREV=0
DUMPED=0
while kill -0 $PID 2>/dev/null; do
  SZ=$(stat -c%s $LOG 2>/dev/null || echo 0)
  T=$(( $(date +%s) - T0 ))
  echo "$T,$SZ" >> $SAMP
  if [ "$SZ" = "$PREV" ] && [ $T -gt 15 ]; then FLAT=$((FLAT+1)); else FLAT=0; fi
  PREV=$SZ
  if [ $FLAT -ge 6 ] && [ $DUMPED -eq 0 ]; then
    DUMPED=1
    echo "=== 冻结检测 t=${T}s (零增长 ${FLAT} 采样) → 取证开始 $(date +%T) ==="
    {
      echo "freeze_at_t=${T}s log_bytes=$SZ timeout_pid=$PID engine_pid=$CHILD"
      echo "--- 线程数 ---"
      ls /proc/$CHILD/task | wc -l
      echo "--- tid comm state wchan ---"
      for d in /proc/$CHILD/task/*; do
        tid=$(basename "$d")
        printf '%s %-20s state=%s wchan=%s\n' "$tid" "$(cat "$d/comm" 2>/dev/null)" \
          "$(awk '{print $3}' "$d/stat" 2>/dev/null)" "$(cat "$d/wchan" 2>/dev/null)"
      done
      echo "--- 日志尾 5 行 ---"
      tail -5 $LOG | cut -c1-160
    } > $PROC 2>&1
    echo "  /proc 快照 → $PROC"
    timeout 120 gdb -p $CHILD -batch -ex 'set pagination off' -ex 'set confirm off' \
      -ex 'thread apply all bt' > $DUMP 2>&1
    echo "  gdb 栈 → $DUMP ($(wc -l < $DUMP) 行)"
  fi
  sleep 2
done
wait $PID; RC=$?
echo "=== rc=$RC 结束 $(date +%T) ==="
tail -2 $LOG | cut -c1-150
echo ""
echo "=== /proc 快照 ==="
[ -f $PROC ] && cat $PROC
echo ""
echo "=== gdb 栈 (前 50 行) ==="
[ -f $DUMP ] && head -50 $DUMP
echo ""
echo "取证文件: $LOG / $PROC / $DUMP / $SAMP"
