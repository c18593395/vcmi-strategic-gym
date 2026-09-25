#!/bin/bash
# 250 步 + gdb 全线程栈取证: 定位池图长局是否 Mode B 冻结 (BuildAnalyzer 读锁)
# 原理: 30s 无日志增长 → 判冻结 → 抓 gdb 全线程栈 + /proc 线程态
set -u
VENV="${VENV:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER="${RUNNER:-/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py}"
B="${B:-/home/administrator/vcmi-native}"
OUT=/tmp/_296_gdb
mkdir -p $OUT
export LD_LIBRARY_PATH=$B/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=$B/rel/bin/libmlclient.so

MAP=${1:-good_to_go_h3m.vmap}
TS=$(date +%H%M%S)
LOG=$OUT/ep250_${MAP%.vmap}_${TS}.log
GDBDUMP=$OUT/gdb_${MAP%.vmap}_${TS}.txt
PROCDUMP=$OUT/proc_${MAP%.vmap}_${TS}.txt

echo "=== [250gdb] $MAP start $(date +%T) ==="
timeout 500 $VENV $RUNNER 250 $OUT/traj.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $LOG 2>&1 &
PID=$!
sleep 3
# 真正跑引擎的子进程
CHILD=$(pgrep -P $PID 2>/dev/null | head -1)
[ -z "$CHILD" ] && CHILD=$PID
echo "  timeout_pid=$PID  engine_pid=$CHILD ($(cat /proc/$CHILD/comm 2>/dev/null))"

T0=$(date +%s)
FLAT=0
PREV=0
DUMPED=0
while kill -0 $PID 2>/dev/null; do
  SZ=$(stat -c%s "$LOG" 2>/dev/null || echo 0)
  T=$(( $(date +%s) - T0 ))
  if [ "$SZ" = "$PREV" ] && [ $T -gt 30 ]; then FLAT=$((FLAT+1)); else FLAT=0; fi
  PREV=$SZ
  if [ $FLAT -ge 15 ] && [ $DUMPED -eq 0 ]; then
    DUMPED=1
    echo "=== 冻结检测 t=${T}s (零增长 15 采样 ≈30s) → 取证开始 $(date +%T) ==="
    {
      echo "freeze_at_t=${T}s log_bytes=$SZ timeout_pid=$PID engine_pid=$CHILD"
      echo "--- 线程数 ---"
      ls /proc/$CHILD/task 2>/dev/null | wc -l
      echo "--- tid comm state wchan ---"
      for d in /proc/$CHILD/task/*; do
        tid=$(basename "$d")
        printf '%s %-20s state=%s wchan=%s\n' "$tid" "$(cat "$d/comm" 2>/dev/null)" \
          "$(awk '{print $3}' "$d/stat" 2>/dev/null)" "$(cat "$d/wchan" 2>/dev/null)"
      done
      echo "--- 日志尾 10 行 ---"
      tail -10 "$LOG" | cut -c1-160
    } > "$PROCDUMP" 2>&1
    echo "  /proc 快照 → $PROCDUMP"
    # gdb 全线程栈 (60s 上限防卡)
    timeout 60 gdb -p $CHILD -batch -ex 'set pagination off' -ex 'set confirm off' \
      -ex 'thread apply all bt' > "$GDBDUMP" 2>&1
    echo "  gdb 栈 → $GDBDUMP ($(wc -l < $GDBDUMP) 行)"
  fi
  sleep 2
done
wait $PID; RC=$?
echo "=== rc=$RC 结束 $(date +%T) ==="
echo "  rc=$RC"
grep -aoE 'steps=[0-9]+' $LOG | head -1
grep -aoE 'secs=[0-9]+' $LOG | head -1
grep -ac 'EP298_SWALLOW' $LOG
grep -ac 'adventure_wait timed out' $LOG
grep -ac 'force game_over' $LOG
echo
echo "=== /proc 快照 ==="
cat $PROCDUMP 2>/dev/null
echo
echo "=== gdb 栈 (前 80 行) ==="
head -80 $GDBDUMP 2>/dev/null
echo
echo "取证文件: $LOG / $PROCDUMP / $GDBDUMP"
