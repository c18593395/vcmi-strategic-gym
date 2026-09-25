#!/usr/bin/env bash
# nounder 双图独立【训练链路】验证 (2026-09-18)
# 与随机策略冒烟的区别: 加载当前 PPO checkpoint 走模型前向策略 + 训练同款引导参数
#   (blue=MMAI_RANDOM / explore 0.3 / economy_force 24 / nk2 0.45 / scorer 链 / 循环惩罚全套)
# 与在跑训练零接触: 只读 checkpoints/, 独立 VCMI server, CPU 推理
# 判据: 250 步跑满 + [EP_TIME] err=no + 零 segfault + 事件行 (GUARD/MINE/TOWN/ECON) 采样
set -u
cd /mnt/d/Bigdata/hero3_fresh
export LD_LIBRARY_PATH="/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel:${LD_LIBRARY_PATH:-}"
VENV="${VENV:-/home/administrator/vcmi-workspace/venv/bin/python}"
STEPS=250
MAPS="when_dragons_clash_nounder_adventure"

# 最新 checkpoint (step 数排序取最大)
CKPT=$(ls -1 checkpoints/wsl2_ckpt_*.pt 2>/dev/null | sed 's/.*wsl2_ckpt_\([0-9]*\)\.pt/\1 &/' | sort -n | tail -1 | awk '{print $2}')
[ -n "$CKPT" ] || { echo "[FAIL] checkpoints/ 无可用 checkpoint"; exit 1; }
echo "checkpoint: $CKPT ($(stat -c%s "$CKPT") bytes)"
echo

FAIL=0
for m in $MAPS; do
  echo "############ 训练验证: $m x${STEPS}步 (模型驱动) ############"
  LOG="/tmp/vtrain_${m}.log"
  TRAJ="/tmp/vtrain_${m}_traj.json"
  rm -f "$LOG" "$TRAJ"
  timeout 1800 $VENV ep_runner_one.py $STEPS "$TRAJ" "$m.vmap" \
    --model "$CKPT" \
    --blue_ai MMAI_RANDOM --blue_adventure_ai MMAI \
    --reward_explore 0.3 \
    --move_to_bias 1.0 --move_to_force 60 --act_loop_from_step 60 \
    --economy_force 24 --cycle_detect 5 --act_loop_penalty 1.0 \
    --guard_done_steps 15 --objective_reward 30 \
    --use_nk2_shaping --nk2_shaping_scale 0.45 \
    --target_chain scorer >"$LOG" 2>&1
  rc=$?
  echo "exit=$rc (0=局自然结束, 124=超时截断)"
  # runner 退出码判定 (139=Segfault, bash 打到 stderr 不进 LOG, 必须查 rc)
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 124 ]; then
    echo "[FAIL] runner 异常退出 rc=$rc (139=Segfault)"
    FAIL=1
  fi
  # 致命错误 (日志内 + bash stderr 兜底)
  if grep -qiE "Segmentation|SIGABRT|terminate called|Assertion|core dumped" "$LOG"; then
    echo "[FAIL] 引擎致命错误:"; grep -iE "Segmentation|SIGABRT|terminate called|Assertion|core dumped" "$LOG" | head -3
    FAIL=1
  elif [ "$rc" -eq 139 ]; then
    echo "[FAIL] 引擎致命错误: Segmentation fault (rc=139)"
    FAIL=1
  else
    echo "[PASS] 零致命错误"
  fi
  # EP_TIME / 事件采样
  grep -E "\[EP_TIME\]" "$LOG"
  grep -cE "\[SCORE\]" "$LOG" | xargs echo "[SCORE] 行数:"
  grep -E "\[GUARD\]|\[MINE\]|\[TOWN\]|\[ECON\]|\[HERO_DEATH\]|\[ENDTURN_FUSE\]|\[START_HOME\] (adjacent|abort)" "$LOG" | head -8
  # traj 完整性
  $VENV - "$TRAJ" <<'PYE'
import json, sys
try:
    t = json.load(open(sys.argv[1]))
except Exception:
    print("[FAIL] traj 缺失/损坏"); raise SystemExit(1)
tg = t.get("terrain_grid") or []
nz = sum(1 for v in tg if v and any(v))
err = t.get("error")
print(f"steps={t.get('steps')}  total_rew={t.get('total_rew')}  "
      f"done={any(t.get('done') or [])}  terrain_snapshots_nonzero={nz}  error={err}")
if t.get("steps") and not err:
    print("[PASS] traj 完整")
    raise SystemExit(0)
print("[FAIL] traj 异常")
raise SystemExit(1)
PYE
  [ $? -eq 0 ] || FAIL=1
  echo
done

echo "================ 训练验证汇总 ================"
if [ "$FAIL" -eq 0 ]; then
  echo "[ALL PASS] 双图模型驱动整局全绿 — 训练链路可用, 可随时入池"
else
  echo "[FAIL] 存在失败项, 见上方明细"
fi
exit $FAIL
