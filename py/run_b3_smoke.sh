#!/usr/bin/env bash
# B3 ep_runner 冒烟: B3 全规则改写产物 (R1 城归零 + R4 白名单 366 对象 + R6 标准胜负 + R7 改名)
# 不碰在跑训练; VCMI server 子进程跑 6 步 (随机策略, 不用 checkpoint 省启动时间)
# 图名含 adventure 关键词 (踩坑 #246)
set -u
cd /mnt/d/Bigdata/hero3_fresh
SRC=/tmp/b3_matrix/default.vmap
DST="${DST:-/home/administrator/vcmi-native/rel/bin/data/Maps/B3_adventure_knee_deep.vmap}"
[ -f "$SRC" ] || { echo "missing $SRC (先跑 run_b3_matrix.sh)"; exit 1; }
cp "$SRC" "$DST"
echo "deployed: $DST ($(stat -c%s "$DST") bytes)"

LOG=/tmp/ep_b3_knee_smoke.log
TRAJ=/tmp/b3_knee_traj.json
rm -f "$LOG" "$TRAJ"
echo "=== smoke start: B3_adventure_knee_deep.vmap x 6 steps ==="
timeout 300 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py 6 "$TRAJ" B3_adventure_knee_deep.vmap >"$LOG" 2>&1
rc=$?
echo "exit=$rc (124=timeout 跑满=正常)"
echo "=== traj ==="
ls -la "$TRAJ" 2>/dev/null
/home/administrator/vcmi-workspace/venv/bin/python - <<'PY'
import json, os
p = "/tmp/b3_knee_traj.json"
if not os.path.exists(p):
    print("traj missing"); raise SystemExit
t = json.load(open(p))
print("mapname:", t.get("mapname"))
print("steps:", t.get("steps"))
print("total_rew:", t.get("total_rew"))
print("done:", t.get("done"))
PY
echo "=== ep log tail ==="
tail -25 "$LOG"
echo "=== ep log 关键行 ==="
grep -iE "loadMap|ENGINE|FAILED|error|exception|segmentation|terminate|assert" "$LOG" | head -20
