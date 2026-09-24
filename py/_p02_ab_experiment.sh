#!/bin/bash
# P0-2 对照实验: 三套 09-23 补丁 A/B 对照（基线 vs 恢复），同 4 图 N≥4
# 用法: bash _p02_ab_experiment.sh {baseline|restored}
#   baseline  = 回退三套补丁 → 重编 → 4图×4轮（验证"冻结从未消失"基线）
#   restored  = 当前态（三套补丁部署）→ 重编 → 4图×4轮（验证修复效果）
# 纪律: 竞态类 N≥4 + 基线对照（09-23 置顶硬规则）

set -u
EXP=${1:-baseline}
B=/home/administrator/vcmi-native
VENV=/home/administrator/vcmi-workspace/venv/bin/python
RUNNER=/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py
OUT=/tmp/_298_ab_${EXP}
mkdir -p $OUT
SUMMARY=$OUT/summary.txt

# 4 张图（与 09-23 _298_verify_sfix.sh 同池，偶发图 elbow/a_viking 在内）
MAPS=(good_to_go_h3m.vmap judgement_day_h3m.vmap elbow_room_h3m.vmap a_viking_we_shall_go_h3m.vmap)
N_ROUNDS=4
STEPS=30

export LD_LIBRARY_PATH=$B/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=$B/rel/bin/libmlclient.so

echo "=== P0-2 对照实验 [$EXP] ==="
echo "  4 图 × $N_ROUNDS 轮, $STEPS 步/局, timeout 300s"
echo "  开始: $(date '+%H:%M:%S')"
echo

if [ "$EXP" = "baseline" ]; then
  echo "--- 回退三套补丁 (rollback) ---"
  python3 /mnt/d/Bigdata/hero3_fresh/py/patch_298_stacktrace.py rollback
  python3 /mnt/d/Bigdata/hero3_fresh/py/patch_298_netthread_fix.py rollback
  python3 /mnt/d/Bigdata/hero3_fresh/py/patch_298_upgrade_probe.py rollback
  echo
  echo "--- 重编 mlclient (CMAKE 必须出现 Building CXX, copy2 保留旧 mtime 让重编变空操作 → 手动 touch 触发) ---"
  # 关键: 补丁 rollback 用 copy2 保留 .bak 旧 mtime，必须 touch 改回后的 .cpp 让 CMAKE 重编
  find $B/client $B/server $B/AI/Nullkiller2 -name '*.cpp' -newer $B/rel/bin/libmlclient.so -exec touch {} \;
  cd $B/rel && cmake --build . --target mlclient -j8 2>&1 | grep -E 'Building CXX|error|Error' | head -20
  echo "  libmlclient.so mtime: $(stat -c '%y' $B/rel/bin/libmlclient.so)"
  echo
elif [ "$EXP" = "restored" ]; then
  echo "--- 当前态(三套已部署) 重编 mlclient (确认重编非空操作) ---"
  find $B/client $B/server $B/AI/Nullkiller2 -name '*.cpp' -exec touch {} \;
  cd $B/rel && cmake --build . --target mlclient -j8 2>&1 | grep -E 'Building CXX|error|Error' | head -20
  echo "  libmlclient.so mtime: $(stat -c '%y' $B/rel/bin/libmlclient.so)"
  echo
else
  echo "未知模式: $EXP (baseline|restored)"
  exit 1
fi

# A/B 跑同 4 图 N≥4
echo "=== 跑 4 图 × $N_ROUNDS 轮 ==="
echo "map,round,rc,steps,secs,swallow,timeout,break" > $SUMMARY
for MAP in "${MAPS[@]}"; do
  for R in $(seq 1 $N_ROUNDS); do
    TS=$(date +%H%M%S)
    ELOG=$OUT/ep_${MAP%.vmap}_${R}_${TS}.log
    timeout 300 $VENV $RUNNER $STEPS /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $ELOG 2>&1
    RC=$?
    STEPS=$(grep -aoE 'steps=[0-9]+' $ELOG | head -1); STEPS=${STEPS#steps=}
    SECS=$(grep -aoE 'secs=[0-9]+' $ELOG | head -1); SECS=${SECS#secs=}
    SW=$(grep -ac 'EP298_SWALLOW' $ELOG 2>/dev/null || echo 0)
    TO=$(grep -ac 'adventure_wait timed out' $ELOG 2>/dev/null || echo 0)
    BRK=$(grep -ac 'ML-upg.*BREAK' $ELOG 2>/dev/null || echo 0)
    echo "$MAP,$R,$RC,${STEPS:-NA},${SECS:-NA},$SW,$TO,$BRK" >> $SUMMARY
    echo "  [$MAP r$R] rc=$RC steps=${STEPS:-NA} secs=${SECS:-NA} swallow=$SW timeout=$TO break=$BRK"
  done
done

echo
echo "=== [$EXP] 汇总 ==="
column -t -s, $SUMMARY 2>/dev/null || cat $SUMMARY
echo
echo "=== 异常率统计 ==="
TOTAL=$(($(wc -l < $SUMMARY) - 1))
ABNORMAL=$(awk -F, '$3!=0 || $6!=0 || $7!=0' $SUMMARY | grep -v '^map,' | wc -l)
echo "  总局数: $TOTAL / 异常(rc≠0 或 swallow>0 或 timeout>0): $ABNORMAL ($((ABNORMAL*100/TOTAL))%)"
echo
echo "=== 完成: $(date '+%H:%M:%S') ==="
echo "  详细日志: $OUT/ep_*.log"
echo "  汇总: $SUMMARY"
