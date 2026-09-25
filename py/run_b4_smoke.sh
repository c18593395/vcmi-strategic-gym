#!/usr/bin/env bash
# B4 ep_runner 冒烟: B4 正式产出 (全规则 R1-R7 含 R2 玩家重配 red=human/blue=ai)
# 不碰在跑训练; VCMI server 子进程跑 6 步 (随机策略, 不用 checkpoint 省启动时间)
# 图名含 adventure 关键词 (踩坑 #246)
set -u
cd /mnt/d/Bigdata/hero3_fresh
SRC=/tmp/b4_out/B4_adventure_knee_deep.vmap
DST="${DST:-/home/administrator/vcmi-native/rel/bin/data/Maps/B4_adventure_knee_deep.vmap}"
[ -f "$SRC" ] || { echo "missing $SRC (先跑 run_b4_verify.sh)"; exit 1; }
cp "$SRC" "$DST"
echo "deployed: $DST ($(stat -c%s "$DST") bytes)"

LOG=/tmp/ep_b4_knee_smoke.log
TRAJ=/tmp/b4_knee_traj.json
rm -f "$LOG" "$TRAJ"
echo "=== smoke start: B4_adventure_knee_deep.vmap x 6 steps ==="
timeout 300 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py 6 "$TRAJ" B4_adventure_knee_deep.vmap >"$LOG" 2>&1
rc=$?
echo "exit=$rc (124=timeout 跑满=正常)"
echo "=== traj ==="
ls -la "$TRAJ" 2>/dev/null
/home/administrator/vcmi-workspace/venv/bin/python - <<'PY'
import json, os
p = "/tmp/b4_knee_traj.json"
if not os.path.exists(p):
    print("traj missing"); raise SystemExit
t = json.load(open(p))
print("mapname:", t.get("mapname"))
print("steps:", t.get("steps"))
print("total_rew:", t.get("total_rew"))
print("done:", t.get("done"))
obs = t.get("obs_final") or {}
tg = obs.get("terrain_grid") or []
nz = sum(1 for v in tg if v)
print("terrain_grid nonzero:", nz)
PY
echo "=== ep log tail ==="
tail -25 "$LOG"
echo "=== ep log 关键行 ==="
grep -iE "loadMap|ENGINE|FAILED|error|exception|segmentation|terminate|assert" "$LOG" | head -20
