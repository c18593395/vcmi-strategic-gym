#!/usr/bin/env bash
# OPS-20260828-01 验收 第二轮：等待 150 秒 (~2.5 min)
set +e
SEC=150
echo "=== wait ${SEC}s begin @ $(date '+%T') ==="
sleep $SEC
echo "=== alive ps @ $(date '+%T') ==="
ps -efH | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '(none)'
echo "=== log lines after RESUME v3 marker (head -120) ==="
awk '/^===== OPS-20260828-01 RESUME v3/,0' /mnt/d/Bigdata/hero3_fresh/train_loop.log | head -120
echo "=== TAIL 35 WHOLE LOG ==="
tail -35 /mnt/d/Bigdata/hero3_fresh/train_loop.log
echo "=== quick regex verification ==="
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
echo -n "(a) Loaded step=153785? "; awk '/^===== OPS-20260828-01 RESUME v3/,0' "$LOG" | grep -c 'Loaded train state (model+optimizer, step=153785)'
echo -n "(b) ep >= 393 (in resume section)? "; awk '/^===== OPS-20260828-01 RESUME v3/,0' "$LOG" | grep -oE ' ep=[0-9]+' | sort -uV | tail -10
echo -n "(c) maps=2 (in resume section)? "; awk '/^===== OPS-20260828-01 RESUME v3/,0' "$LOG" | grep -c 'maps=2'
echo -n "(d) [ZOMBIE] or [ENDTURN_FUSE] (in resume section)? "; awk '/^===== OPS-20260828-01 RESUME v3/,0' "$LOG" | grep -cE '\[ZOMBIE\]|\[ENDTURN_FUSE\]'
echo -n "(e) ep_steps values in resume section? "; awk '/^===== OPS-20260828-01 RESUME v3/,0' "$LOG" | grep -oE 'ep_steps=[0-9]+' | sort -u | head -10
echo -n "   most recent 15 ep_steps lines: "; awk '/^===== OPS-20260828-01 RESUME v3/,0' "$LOG" | grep -oE 'ep_steps=[0-9]+ r=[-0-9.]+' | tail -15
