#!/usr/bin/env bash
# OPS-20260828-01 验收 v3：等待 8 分钟，给足够多 ep 出 ZOMBIE/ENDTURN_FUSE + 非200 ep_steps
set +e
SEC=480
echo "=== wait ${SEC}s begin @ $(date '+%Y-%m-%d %T') ==="
sleep $SEC
echo "=== alive ps @ $(date '+%T') ==="
ps -efH | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '(DEAD!)'
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
MARK='^===== OPS-20260828-01 RESUME v3'
echo "=== tail 30 WHOLE LOG ==="
tail -30 "$LOG"
echo "=== 5 criteria check ==="
echo -n "(a) Loaded step=153785?  cnt="; awk "/$MARK/,0" "$LOG" | grep -c 'Loaded train state (model+optimizer, step=153785)'
echo    "    samples:"; awk "/$MARK/,0" "$LOG" | grep 'Loaded train state' | head -3
echo -n "(b) ep list after resume (unique, tail-15): "; awk "/$MARK/,0" "$LOG" | grep -oE ' ep=[0-9]+' | sort -uV | tail -15
echo -n "    ep_count_lines_after_resume="; awk "/$MARK/,0" "$LOG" | grep -cE 'step[0-9]+ avg_r.* ep='
echo -n "(c) maps=2 count="; awk "/$MARK/,0" "$LOG" | grep -c 'maps=2'
echo    "    sample banner:"; awk "/$MARK/,0" "$LOG" | grep 'maps=' | head -3
echo -n "(d) [ZOMBIE] or [ENDTURN_FUSE] count="; awk "/$MARK/,0" "$LOG" | grep -cE '\[ZOMBIE\]|\[ENDTURN_FUSE\]'
echo    "    sample:"; awk "/$MARK/,0" "$LOG" | grep -E '\[ZOMBIE\]|\[ENDTURN_FUSE\]' | head -5
echo -n "(e) unique ep_steps values in resume section="; awk "/$MARK/,0" "$LOG" | grep -oE 'ep_steps=[0-9]+' | sort -u | tr '\n' ' '; echo
echo    "    last 12 ep_steps / r :"; awk "/$MARK/,0" "$LOG" | grep -oE 'ep_steps=[0-9]+ r=[-0-9.]+' | tail -12
