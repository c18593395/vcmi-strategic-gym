#!/usr/bin/env bash
# 去地下 2 图 ep_runner 冒烟 (2026-09-18)
# 部署 rel/bin/data/Maps + 各跑 6 步随机策略, 不碰在跑训练 (run_b4_smoke.sh 同款流程)
set -u
cd /mnt/d/Bigdata/hero3_fresh
MAPS="when_dragons_clash_nounder_adventure unexpected_inheritance_nounder_adventure"

for m in $MAPS; do
  SRC="maps/h3m_to_vmap/$m.vmap"
  DST="${DST:-/home/administrator/vcmi-native/rel/bin/data/Maps/$m.vmap}"
  [ -f "$SRC" ] || { echo "missing $SRC"; exit 1; }
  cp "$SRC" "$DST"
  echo "deployed: $m ($(stat -c%s "$DST") bytes)"
done

for m in $MAPS; do
  LOG="/tmp/ep_${m}.log"
  TRAJ="/tmp/${m}_traj.json"
  rm -f "$LOG" "$TRAJ"
  echo "=== smoke: $m x6 steps ==="
  timeout 300 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py 6 "$TRAJ" "$m.vmap" >"$LOG" 2>&1
  echo "exit=$? (124=timeout 跑满=正常窗口)"
  /home/administrator/vcmi-workspace/venv/bin/python - "$TRAJ" <<'PY'
import json, sys
try:
    t = json.load(open(sys.argv[1]))
except Exception:
    print("traj missing")
    raise SystemExit
print("mapname:", t.get("mapname"), "| steps:", t.get("steps"),
      "| total_rew:", t.get("total_rew"), "| done:", t.get("done"))
obs = t.get("obs_final") or {}
tg = obs.get("terrain_grid") or []
print("terrain_grid nonzero:", sum(1 for v in tg if v))
PY
  echo "--- 引擎关键行 ---"
  grep -iE "Grouped|visitLobby|FAILED|error|exception|Segmentation|terminate|assert" "$LOG" | head -10
  echo
done
