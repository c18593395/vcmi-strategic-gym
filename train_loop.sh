#!/bin/bash
# ARM64 24/7 training loop — StrategicEnv PPO
# Usage: nohup bash train_loop.sh > train.log 2>&1 &

cd /DATA/hero3
export LD_LIBRARY_PATH="/DATA/hero3/vcmi-build/bin:/tmp/onnxruntime/lib"

# Map rotation: anchor on adventure-A1, cycle through others
MAPS=(
  "adventure-A1.vmap"
  "adventure-A1.vmap"
  "adventure-A1.vmap"
)

MODEL_DIR="/DATA/hero3/models/strategic_ppo"
mkdir -p "$MODEL_DIR"

ROUND=0
while true; do
  MAP="${MAPS[$((ROUND % ${#MAPS[@]}))]}"
  STEPS=10000  # per round

  echo "=== ROUND $ROUND | MAP=$MAP | STEPS=$STEPS | $(date) ==="

  pkill -9 vcmiserver 2>/dev/null
  sleep 2

  VCMI_MAP="$MAP" VCMI_STEPS="$STEPS" python3 -u test_strategic_ppo.py 2>&1

  echo "=== ROUND $ROUND DONE | $(date) ==="
  ROUND=$((ROUND + 1))
  sleep 3
done
