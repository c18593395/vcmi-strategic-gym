#!/usr/bin/env bash
# nounder 双图独立验证 (2026-09-18)
# 判据链: ① vmap zip 结构校验 (h3m2vmap verify)
#         ② 引擎级读回 + 50 步随机策略独立局 (ep_runner_one.py, 不碰在跑训练)
#         ③ traj 完整性: steps 跑满 / terrain_grid 旁路非零 / 零致命错误
# 全绿输出 [PASS], 任一失败输出 [FAIL] 且 rc=1
set -u
cd /mnt/d/Bigdata/hero3_fresh
PY="${PY:-/home/administrator/vcmi-workspace/venv/bin/python}"
MAPS="when_dragons_clash_nounder_adventure unexpected_inheritance_nounder_adventure"
STEPS=50
FAIL=0

for m in $MAPS; do
  echo "############ $m ############"
  SRC="maps/training/$m.vmap"
  DST="${DST:-/home/administrator/vcmi-native/rel/bin/data/Maps/$m.vmap}"
  # 0) 源文件在位
  if [ ! -f "$SRC" ]; then echo "[FAIL] 缺源: $SRC"; FAIL=1; continue; fi
  # 1) 结构校验
  if $PY py/h3m2vmap.py verify "$SRC" | tail -1 | grep -q "^OK"; then
    echo "[PASS] ① verify 结构校验"
  else
    echo "[FAIL] ① verify 结构校验"; FAIL=1; continue
  fi
  # 2) 部署最新副本 + 引擎独立局
  cp "$SRC" "$DST"
  LOG="/tmp/verify_${m}.log"; TRAJ="/tmp/verify_${m}_traj.json"
  rm -f "$LOG" "$TRAJ"
  timeout 900 $PY ep_runner_one.py $STEPS "$TRAJ" "$m.vmap" >"$LOG" 2>&1
  rc=$?
  echo "ep_runner exit=$rc (0=自然跑满, 124=超时截断)"
  # 3) traj 完整性
  $PY - "$TRAJ" "$STEPS" <<'PYE'
import json, sys
p, want = sys.argv[1], int(sys.argv[2])
try:
    t = json.load(open(p))
except Exception:
    print("[FAIL] ③ traj 缺失/损坏"); raise SystemExit(1)
steps = t.get("steps") or 0
tg = t.get("terrain_grid") or []
nz = sum(1 for v in tg if v)
done_any = any(t.get("done") or [])
print(f"steps={steps}/{want}  total_rew={t.get('total_rew')}  done_any={done_any}")
print(f"terrain_grid nonzero={nz}")
ok = True
if steps < want:
    print("[FAIL] ③ 步数未跑满"); ok = False
if nz <= 0:
    print("[FAIL] ③ terrain_grid 旁路全零"); ok = False
print("[PASS] ③ traj 完整性" if ok else "[FAIL] ③ traj 完整性")
raise SystemExit(0 if ok else 1)
PYE
  [ $? -eq 0 ] || FAIL=1
  # 4) 致命错误扫描 (music 缺失为已知良性噪声)
  if grep -qiE "Segmentation|SIGABRT|terminate called|Assertion|core dumped" "$LOG"; then
    echo "[FAIL] ④ 引擎致命错误:"; grep -iE "Segmentation|SIGABRT|terminate called|Assertion|core dumped" "$LOG" | head -3
    FAIL=1
  else
    echo "[PASS] ④ 零致命错误 (Segmentation/ABRT/Assert 无)"
  fi
  echo
done

echo "================ 汇总 ================"
if [ "$FAIL" -eq 0 ]; then echo "[ALL PASS] 两张 nounder 图独立验证全绿, 可随时入池"
else echo "[FAIL] 存在失败项, 见上方明细"; fi
exit $FAIL
