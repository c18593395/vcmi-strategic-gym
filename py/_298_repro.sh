#!/bin/bash
# #298 复现探针 (停训窗执行, 09-23 备料): batch1 三图 × 3 局, red=StupidAI 隔离 ML 模型变量
# 产物: /tmp/_298_evidence/ 每局独立日志 + VCMI_Client_log 归档 + 汇总表
# 用法: wsl -u root systemctl stop homm3-train-v5 后手动执行:
#   wsl bash /mnt/d/Bigdata/hero3_fresh/py/_298_repro.sh
# 预计 ~10-15 分钟 (每局 30 步正常 ~40s, 卡死局 400s 超时)
set -u
OUT=/tmp/_298_evidence
mkdir -p $OUT
PY="${PY:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER="${RUNNER:-/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py}"
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

# 0) 地图运行时同步校验 (--check 只校验不写)
echo "=== [0] 地图同步校验 ==="
$PY /mnt/d/Bigdata/hero3_fresh/py/sync_maps_to_runtime.py --check || { echo "!! 同步校验 rc!=0, 先跑 --strict 再复测"; exit 1; }

MAPS="good_to_go_h3m.vmap judgement_day_h3m.vmap elbow_room_h3m.vmap a_viking_we_shall_go_h3m.vmap"
REPEAT=3
SUMMARY=$OUT/summary.txt
: > $SUMMARY
echo "map,run,rc,steps,secs,query_neg1,cannot_end_turn,fishy,hero_seg_empty,segfault" >> $SUMMARY

for MAP in $MAPS; do
  for i in 1 2 3; do
    [ $i -gt $REPEAT ] && break
    TS=$(date +%H%M%S)
    TAG="${MAP%.vmap}_r${i}_${TS}"
    ELOG=$OUT/ep_${TAG}.log
    echo "=== [$MAP run$i] $(date +%T) start ==="
    # 清 VCMI 引擎文件日志 (每局独立取证)
    CL=/home/administrator/vcmi-native/data/VCMI_Client_log.txt
    [ -f $CL ] && cp $CL ${OUT}/vcmi_client_prev.log 2>/dev/null
    timeout 400 $PY $RUNNER 30 /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $ELOG 2>&1
    RC=$?
    STEPS=$(grep -aoE 'EP_TIME.*steps=([0-9]+)' $ELOG | grep -oE 'steps=[0-9]+' | head -1)
    STEPS=${STEPS#steps=}
    SECS=$(grep -aoE 'EP_TIME.*secs=([0-9]+)' $ELOG | grep -oE 'secs=[0-9]+' | head -1)
    SECS=${SECS#secs=}
    # 引擎文件日志本局增量段取证 (prev 是本局前快照; 若引擎每局覆盖则直接整份)
    Q1=$(grep -ac 'Cannot answer the query -1' $CL 2>/dev/null || echo 0)
    CET=$(grep -ac 'Can not end turn' $CL 2>/dev/null || echo 0)
    FISHY=$(grep -ac 'fishy' $CL 2>/dev/null || echo 0)
    HSE=$(grep -ac 'HEROSEG_EMPTY' $ELOG 2>/dev/null || echo 0)
    SG=$(grep -ac 'Segmentation fault' $ELOG 2>/dev/null || echo 0)
    dmesg 2>/dev/null | tail -50 | grep -q "segfault" && SG=$SG"dmesg"
    echo "$MAP,$i,$RC,${STEPS:-NA},${SECS:-NA},$Q1,$CET,$FISHY,$HSE,$SG" >> $SUMMARY
    # 归档引擎日志快照
    cp $CL ${OUT}/vcmi_client_${TAG}.log 2>/dev/null
    echo "    rc=$RC steps=${STEPS:-NA} secs=${SECS:-NA} q-1=$Q1 endturn=$CET fishy=$FISHY seg=$SG"
  done
done

echo ""
echo "=== 汇总 ==="
column -t -s, $SUMMARY 2>/dev/null || cat $SUMMARY
echo ""
echo "证据目录: $OUT (ep_*.log 每局 runner 全量 / vcmi_client_*.log 引擎文件日志快照)"
echo "下一层: 对失败局 grep -E 'Cannot answer|pickRandomObject|randomizeFaction' vcmi_client_*.log 定型阶段定位"
