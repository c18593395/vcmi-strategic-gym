#!/usr/bin/env bash
# 等待 1 个新的 batch 指标行 (ent/entc/loss), 每 10 分钟轮询一次, 最多 72 次 (12h)
# resume 时间基准: ~18:42
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
BASE=$(grep -an 'ent=' "$LOG" | tail -n 1 | cut -d: -f1)
echo "[watch] baseline ent line @ $BASE $(sed -n "${BASE}p" "$LOG" 2>/dev/null | tr -d ' ')"
for i in $(seq 1 72); do
  sleep 600
  ST=$(systemctl is-active homm3-train-v5)
  if [ "$ST" != "active" ]; then
    echo "[watch] service=$ST at poll $i, dumping tail:"
    tail -n 30 "$LOG"
    exit 1
  fi
  CUR=$(grep -an 'ent=' "$LOG" | tail -n 1 | cut -d: -f1)
  NEW=$(grep -an 'avg_r=' "$LOG" | tail -n 3)
  if [ "$CUR" -gt "$BASE" ] 2>/dev/null && [ -n "$CUR" ]; then
    echo "[watch] NEW ent line appeared @ poll $i ($(date)):"
    sed -n "${CUR}p" "$LOG"
    echo "-- last avg_r lines --"
    echo "$NEW"
    exit 0
  fi
  echo "[watch] poll $i @ $(date +%H:%M) | svc=$ST | ent_line=$CUR (base=$BASE) | last avg_r: $(echo "$NEW" | tail -n 1)"
  if [ "$i" -ge 72 ]; then
    echo "[watch] 12h limit, no new ent line yet"
    tail -n 10 "$LOG"
    exit 0
  fi
done
