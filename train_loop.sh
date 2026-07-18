#!/bin/bash
cd /DATA/hero3
export LD_LIBRARY_PATH="/DATA/hero3/vcmi-build/bin:/tmp/onnxruntime/lib"

MAPS=(
  adventure-A1.vmap
  A1.vmap
  A2.vmap
  A3.vmap
  A4.vmap
  A5.vmap
  A6.vmap
  A7.vmap
  ml-mini.vmap
  ml-train.vmap
)

ROUND=0
while true; do
  MAP="${MAPS[$((ROUND % ${#MAPS[@]}))]}"
  STEPS=10000
  echo "=== ROUND $ROUND | MAP=$MAP | STEPS=$STEPS | $(date) ==="
  pkill -9 vcmiserver 2>/dev/null
  sleep 2
  VCMI_MAP="$MAP" VCMI_STEPS="$STEPS" python3 -u test_strategic_ppo.py 2>&1
  echo "=== ROUND $ROUND DONE | $(date) ==="
  ROUND=$((ROUND + 1))
  sleep 3
done
