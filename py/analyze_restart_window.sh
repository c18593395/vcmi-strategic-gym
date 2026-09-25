#!/usr/bin/env bash
# 分析 homm3-train-v5 本次重启窗口（L76382 起）训练日志
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
START=76382

echo "=== 重启窗口 (L${START} 起) 统计 ==="
echo "文件总行数: $(wc -l < "$LOG")"
echo
echo "[EP_TIME] 局数: $(awk -v s=$START 'NR>s && /\[EP_TIME\]/' "$LOG" | wc -l)"
echo "TOWN_BLOCKED: $(awk -v s=$START 'NR>s && /TOWN_BLOCKED/' "$LOG" | wc -l)"
echo "TOWNSTALL: $(awk -v s=$START 'NR>s && /TOWNSTALL/' "$LOG" | wc -l)"
echo "TOWN_CAPTURE: $(awk -v s=$START 'NR>s && /TOWN_CAPTURE/' "$LOG" | wc -l)"
echo "HERO_DEATH: $(awk -v s=$START 'NR>s && /HERO_DEATH/' "$LOG" | wc -l)"
echo "ZOMBIE: $(awk -v s=$START 'NR>s && /\[ZOMBIE\]/' "$LOG" | wc -l)"
echo "ENDTURN_FUSE: $(awk -v s=$START 'NR>s && /ENDTURN_FUSE/' "$LOG" | wc -l)"
echo "step 推进: $(awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ {match($0, /step([0-9]+)/, a); last=a[1]}' "$LOG" | tail -1)"
echo
echo "=== 窗口内 [EP_TIME] 明细 (行号: map/steps/r/err) ==="
awk -v s=$START 'NR>s && /\[EP_TIME\]/ {print NR": "$0}' "$LOG"
echo
echo "=== 窗口内 r 分布 ==="
awk -v s=$START 'NR>s && /\[EP_TIME\]/ {match($0, /r=([0-9.-]+)/, m); print m[1]}' "$LOG" | sort -n | awk '{sum+=$1; n++; if($1<min||n==1)min=$1; if($1>max||n==1)max=$1} END{if(n>0) printf "n=%d min=%.1f max=%.1f avg=%.1f\n", n, min, max, sum/n; else print "无 EP_TIME"}'
echo
echo "=== 窗口内 r<0 局 ==="
awk -v s=$START 'NR>s && /\[EP_TIME\]/ {match($0, /r=([0-9.-]+)/, m); if(m[1]<0) print NR": "$0}' "$LOG"
