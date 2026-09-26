#!/bin/bash
# RECRUITED 修复验证冒烟 (09-27, WSL libvcmi.so 4def2de6 带 dst=cur 修复)
# 图选择: judgement_day_h3m (H3M 有兵源, 服务器实证 RECRUITED=33) — duel 图无 built dwellings 必为 0 (第二层根因, 非本验证目标)
# ep_runner 位置参数: [max_turns] [outfile] [mapname]
# 用法: bash py/recruit_fix_verify_smoke.sh [地图名] [局数]
set -uo pipefail
export XDG_DATA_HOME=/home/administrator/.local/share
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export LC_ALL=C
cd /home/administrator/vcmi-workspace
PY=/home/administrator/vcmi-workspace/venv/bin/python
RUNNER=/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py
MAP="${1:-judgement_day_h3m.vmap}"
N="${2:-3}"

echo "libvcmi.so md5: $(md5sum /home/administrator/vcmi-native/rel/bin/libvcmi.so | cut -d' ' -f1) (期望 4def2de6*=修复版)"
echo "地图: $MAP  局数: $N"
echo

TOTAL_R=0; TOTAL_T=0; TOTAL_E=0
for i in $(seq 1 "$N"); do
  OUT=/tmp/rfix_out_$i.json
  LOG=/tmp/rfix_$i.log
  T0=$(date +%s)
  timeout 900 $PY $RUNNER \
    250 "$OUT" "$MAP" \
    --blue_adventure_ai Nullkiller2 \
    --model /mnt/d/Bigdata/hero3_fresh/wsl2_model.pt \
    --target_chain scorer \
    --objective_reward 30 \
    --act_loop_penalty 1.0 \
    --monster_mask 1 \
    --use_nk2_shaping \
    > "$LOG" 2>&1
  RC=$?
  T1=$(date +%s)
  R=$(grep -c '\[RECRUITED\]' "$LOG" 2>/dev/null)
  T=$(grep -c '\[TOWN_RETRY\]' "$LOG" 2>/dev/null)
  E=$(grep -c 'ECON. recruit' "$LOG" 2>/dev/null)
  TOTAL_R=$((TOTAL_R+R)); TOTAL_T=$((TOTAL_T+T)); TOTAL_E=$((TOTAL_E+E))
  echo "run$i: rc=$RC secs=$((T1-T0))  RECRUITED=$R TOWN_RETRY=$T ECON_recruit=$E"
  grep '\[RECRUITED\]' "$LOG" | head -3 | sed 's/^/    /'
  grep 'EP_TIME' "$LOG" | tail -1 | sed 's/^/    /'
  echo
done
echo "===== 汇总: RECRUITED 总=$TOTAL_R (ECON_recruit 总=$TOTAL_E, TOWN_RETRY 总=$TOTAL_T) ====="
if [ "$TOTAL_R" -gt 0 ]; then
  echo "✅ RECRUITED 首非零 — WSL 取兵链路修复生效"
else
  echo "❌ RECRUITED 仍 0 (ECON=$TOTAL_E) — 检查 libvcmi.so 是否新编 / 地图是否有兵源"
fi
