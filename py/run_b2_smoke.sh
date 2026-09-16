#!/usr/bin/env bash
# B2 ep_runner 冒烟: B2_KneeDeep.vmap (零改写直通产物)
# 不碰在跑训练; VCMI server 子进程跑 6 步 (随机策略, 不用 checkpoint 省启动时间)
set -u
cd /mnt/d/Bigdata/hero3_fresh
LOG=/tmp/ep_b2_knee_smoke.log
rm -f "$LOG"
echo "=== smoke start: B2_adventure_knee_deep.vmap x 6 steps ==="
timeout 300 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py 6 /tmp/b2_knee_traj.json B2_adventure_knee_deep.vmap >"$LOG" 2>&1
rc=$?
echo "exit=$rc"
echo "=== traj ==="
ls -la /tmp/b2_knee_traj.json 2>/dev/null
/home/administrator/vcmi-workspace/venv/bin/python - <<'PY'
import json, os
p = "/tmp/b2_knee_traj.json"
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
echo "=== ep log load/loadMap 关键行 ==="
grep -iE "loadMap|ENGINE|FAILED|error|exception|segmentation|terminate|assert" "$LOG" | head -20
