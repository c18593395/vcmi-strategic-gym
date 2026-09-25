#!/bin/bash
# T06 窗口定量体检 (只读, 09-11)
L="${L:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
echo '=== T06 duel EP_TIME aggregate (recent 30) ==='
grep "EP_TIME.*72X72_01_duel" "$L" | tail -30 | sed -E 's/.*steps=([0-9]+) secs=([0-9]+) r=([-0-9.]+).*/\1 \2 \3/' | \
awk '{s+=$1; sr+=$3; c200+=($1>=198); if(NR==1||$1<min)min=$1; if($1>max)max=$1; if($3>maxr)maxr=$3; if(NR==1||$3<minr)minr=$3; n++} END{printf "n=%d steps[min=%d max=%d avg=%.1f] r[min=%.1f max=%.1f avg=%.1f] cap_hit(>=198)=%d/%d\n", n, min, max, s/n, minr, maxr, sr/n, c200, n}'
echo '=== T06 1v3 EP_TIME (recent 10) ==='
grep "EP_TIME.*72X72_01.vmap" "$L" | grep -v duel | tail -10 | sed -E 's/.*steps=([0-9]+) secs=([0-9]+) r=([-0-9.]+).*/\1 \2 \3/'
echo '=== last 5000 lines marks ==='
tail -5000 "$L" | grep -o 'ZOMBIE' | wc -l
tail -5000 "$L" | grep -o 'ENDTURN_FUSE' | wc -l
echo '=== last 30 ep step/r summary (any map) ==='
grep -o 'ep_steps=[0-9]* r=[-0-9.]*' "$L" | tail -30
echo '=== service since ==='
systemctl status homm3-train-v5 --no-pager 2>/dev/null | head -6
