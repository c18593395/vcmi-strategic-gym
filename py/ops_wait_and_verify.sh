#!/usr/bin/env bash
# OPS-20260828-01 验收检查：等待50秒后打印尾部30行+进程存活确认
set +e
echo "=== wait 50s @ $(date '+%T') ==="
sleep 50
echo "=== alive ps @ $(date '+%T') ==="
ps -efH | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '(none)'
echo "=== train_loop.log tail -30 @ $(date '+%T') ==="
tail -30 /mnt/d/Bigdata/hero3_fresh/train_loop.log
echo "=== quick regex verification ==="
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
echo -n "(a) Loaded train state? "; grep -c 'Loaded train state (model+optimizer, step=153785)' "$LOG"
echo -n "(b) ep >= 393? "; grep -oE ' ep=[0-9]+' "$LOG" | tail -5 || echo '(no ep lines yet)'
echo -n "(c) maps=2 banner? "; grep -c 'maps=2' "$LOG"
echo -n "(d) ZOMBIE or ENDTURN_FUSE? "; grep -cE '\[ZOMBIE\]|\[ENDTURN_FUSE\]' "$LOG"
echo -n "(e) non-200 ep_steps (last 20 ep lines)? "; grep -oE 'ep_steps=[0-9]+' "$LOG" | tail -20 | sort -u
