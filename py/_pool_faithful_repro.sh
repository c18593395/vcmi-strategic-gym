#!/bin/bash
# 忠实复现: 逐字照抄训练实参(含 --model)在池图上跑, 抓 traj 丢失根因
VENV=/home/administrator/vcmi-workspace/venv/bin/python
RUNNER=/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py
B=/home/administrator/vcmi-native
export LD_LIBRARY_PATH=$B/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=$B/rel/bin/libmlclient.so

OUT=/tmp/_pool_faithful
mkdir -p "$OUT"

CKPT=$(ls -t /mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_ckpt_*.pt 2>/dev/null | head -1)
echo "=== CKPT=$CKPT (size=$(stat -c%s "$CKPT" 2>/dev/null || echo NA)) ==="
[ -z "$CKPT" ] && { echo "无 checkpoint, 退出"; exit 1; }

MAP=${1:-good_to_go_h3m.vmap}
STEPS=${2:-30}
RUNS=${3:-2}
TMO=${TMO:-$((STEPS * 3 + 220))}   # 250 步 → 970s; 30 步 → 310s

for i in $(seq 1 $RUNS); do
  TRAJ=$OUT/traj_$i.json
  rm -f "$TRAJ"
  echo "--- [run $i] $MAP steps=$STEPS timeout=${TMO}s $(date +%T) ---"
  timeout $TMO $VENV $RUNNER $STEPS "$TRAJ" "$MAP" \
    --model "$CKPT" --blue_ai MMAI_RANDOM --blue_adventure_ai MMAI \
    --blue_hero_attack_bypass 1 --blue_hero_contact_d 2 --attack_f_min 0.0 \
    --reward_explore 0.3 --move_to_bias 1.95 --move_to_force 29 --economy_force 24 \
    --cycle_detect 5 --act_loop_penalty 1.0 --guard_done_steps 15 --objective_reward 30 \
    --use_nk2_shaping --nk2_shaping_scale 0.45 --target_chain scorer \
    > "$OUT/log_$i.txt" 2>&1
  RC=$?
  SZ=$(stat -c%s "$TRAJ" 2>/dev/null || echo 0)
  echo "  rc=$RC  traj_exists=$([ -f "$TRAJ" ] && echo YES || echo NO)  traj_size=$SZ"
  echo "  EP_TIME: $(grep -a 'EP_TIME' "$OUT/log_$i.txt" | head -1)"
  echo "  日志总行: $(wc -l < "$OUT/log_$i.txt")"
  echo "  尾部 6 行:"
  tail -6 "$OUT/log_$i.txt" | cut -c1-160
  echo "  关键标记 (abort/terminate/what/query):"
  grep -aE 'terminate called|what\(\)|Aborted|abort|unanswered query|has to answer|SHUTDOWN|SIGABRT|pure virtual|bad_alloc|std::' "$OUT/log_$i.txt" | tail -20 | cut -c1-200
  echo "  EP_TIME / 错误标记:"
  grep -aE 'EP_TIME|EP298_SWALLOW|RED_DEAD|Traceback' "$OUT/log_$i.txt" | tail -5 | cut -c1-200
  echo
  echo
done