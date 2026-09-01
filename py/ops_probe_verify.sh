#!/usr/bin/env bash
# OPS-20260828-01 探测验收（直接）
set +e
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
MARK='RESUME v3'
echo '=== size & mtime ==='
stat -c 'mtime=%y size=%s' "$LOG"
echo '=== ps alive ==='
ps -efH | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '(none)'
echo '=== lines after RESUME v3 (last 40) ==='
awk '/RESUME v3/,0' "$LOG" | tail -40
echo '=== 5 criteria ==='
SECTION=$(awk '/RESUME v3/,0' "$LOG")
echo -n "(a) Loaded step=153785 count = "; echo "$SECTION" | grep -c 'Loaded train state (model+optimizer, step=153785)'
echo    "    sample: "; echo "$SECTION" | grep 'Loaded train state' | head -3
echo -n "(b) ep unique after resume = "; echo "$SECTION" | grep -oE ' ep=[0-9]+' | sort -uV | tr '\n' ' '; echo
echo -n "    total ep step lines = "; echo "$SECTION" | grep -cE 'step[0-9]+ avg_r.* ep='
echo -n "(c) maps=2 count = "; echo "$SECTION" | grep -c 'maps=2'
echo    "    banner sample: "; echo "$SECTION" | grep 'maps=' | head -3
echo -n "(d) [ZOMBIE] or [ENDTURN_FUSE] count = "; echo "$SECTION" | grep -cE '\[ZOMBIE\]|\[ENDTURN_FUSE\]'
echo    "    samples: "; echo "$SECTION" | grep -E '\[ZOMBIE\]|\[ENDTURN_FUSE\]' | head -5
echo -n "(e) ep_steps unique values = "; echo "$SECTION" | grep -oE 'ep_steps=[0-9]+' | sort -u | tr '\n' ' '; echo
echo    "last 10 ep_steps r lines: "; echo "$SECTION" | grep -oE 'ep_steps=[0-9]+ r=[-0-9.]+' | tail -10
echo "=== DONE ==="
