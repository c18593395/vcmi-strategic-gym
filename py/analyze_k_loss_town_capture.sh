#!/usr/bin/env bash
# 分析 k=10.0 顶格 / loss spike / vloss / TOWN_CAPTURE 频率
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
# 重启窗口起点 (L877 修复后 resume)
START=76382

echo "=== 重启后窗口 (L${START} 起, 截至文件尾) ==="
echo "文件总行数: $(wc -l < "$LOG")"
echo

echo "=== 1. step 行带 k / loss / vloss 的明细 ==="
echo "(k=10.0 顶格, loss spike, vloss 趋势)"
awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ {print NR": "$0}' "$LOG" | tail -60
echo

echo "=== 2. k=10.0 持续顶格统计 ==="
echo "窗口内 k=10.0 行数: $(awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ && /k=10\.0/' "$LOG" | wc -l)"
echo "窗口内 step 行总数: $(awk -v s=$START 'NR>s && /step[0-9]+ avg_r/' "$LOG" | wc -l)"
echo "窗口内 k<10 的 step 行: $(awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ && !/k=10\.0/' "$LOG" | wc -l)"
echo
echo "k 值分布 (窗口内 step 行):"
awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ {match($0, /k=([0-9.]+)/, m); if(m[1]!="") print m[1]}' "$LOG" | sort | uniq -c | sort -rn
echo

echo "=== 3. loss 跳升 (loss>5) ==="
echo "窗口内 loss>5 的 step 行:"
awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ {match($0, /loss=([0-9.]+)/, m); if(m[1]!="" && m[1]>5) print NR": "$0}' "$LOG"
echo
echo "loss 值分布 (窗口内 step 行):"
awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ {match($0, /loss=([0-9.]+)/, m); if(m[1]!="") print m[1]}' "$LOG" | sort -n | awk '{a[NR]=$1} END{if(NR>0){print "min="a[1], "max="a[NR], "median="a[int(NR/2)]; n=0; for(i=1;i<=NR;i++) if(a[i]>5) n++; printf "loss>5 行数: %d/%d (%.0f%%)\n", n, NR, n*100/NR}}'
echo

echo "=== 4. vloss 趋势 ==="
echo "窗口内 vloss 明细 (抽样):"
awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ {match($0, /vloss=([0-9.]+)/, m); if(m[1]!="") print NR": vloss="m[1]}' "$LOG" | head -30
echo "vloss 分布:"
awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ {match($0, /vloss=([0-9.]+)/, m); if(m[1]!="") print m[1]}' "$LOG" | sort -n | awk '{sum+=$1; n++; if($1<min||n==1)min=$1; if($1>max||n==1)max=$1} END{if(n>0) printf "n=%d min=%.3f max=%.3f avg=%.3f\n", n, min, max, sum/n}'
echo

echo "=== 5. TOWN_CAPTURE 频率 ==="
echo "窗口内 TOWN_CAPTURE 总次数: $(awk -v s=$START 'NR>s && /TOWN_CAPTURE/' "$LOG" | wc -l)"
echo "窗口内 [EP_TIME] 局数: $(awk -v s=$START 'NR>s && /\[EP_TIME\]/' "$LOG" | wc -l)"
echo "窗口内 TOWN_CAPTURE 明细 (行号 + step):"
awk -v s=$START 'NR>s && /TOWN_CAPTURE/ {print NR": "$0}' "$LOG"
echo
echo "按地图统计 TOWN_CAPTURE:"
awk -v s=$START 'NR>s && /TOWN_CAPTURE/ {match($0, /map=([A-Za-z0-9_.]+)/, m); print m[1]}' "$LOG" | sort | uniq -c | sort -rn
echo

echo "=== 6. KL 值 (若 step 行含 kl=) ==="
echo "窗口内 kl 值分布:"
awk -v s=$START 'NR>s && /step[0-9]+ avg_r/ {match($0, /kl=([0-9.]+)/, m); if(m[1]!="") print m[1]}' "$LOG" | sort | uniq -c | sort -rn
echo

echo "=== 7. 近期 EP_TIME (窗口内 T06 局) ==="
awk -v s=$START 'NR>s && /\[EP_TIME\]/ && /T06/ {print NR": "$0}' "$LOG"
