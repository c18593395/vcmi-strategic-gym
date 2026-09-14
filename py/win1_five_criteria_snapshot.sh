#!/bin/bash
# WIN-1 五判据聚合快照（09-15 S2 部署前置核查）
cd /mnt/d/Bigdata/hero3_fresh
LOG=train_loop.log

echo "=== 本次窗启动时间 ==="
systemctl show homm3-train-v5 --property=ActiveEnterTimestamp --value 2>/dev/null

echo "=== 日志 mtime ==="
stat -c '%y' "$LOG"

echo "=== [ENDTURN] 局数 ==="
grep -c 'ENDTURN' "$LOG"

echo "=== 近 40 局 avg_r ==="
grep -o 'avg_r=[-0-9.]*' "$LOG" | tail -40 | grep -o '[-0-9.]*' | awk '{s+=$1;n++} END {if(n>0) printf "n=%d avg_r=%.2f\n", n, s/n; else print "无数据"}'

echo "=== 全窗 TOWN_CAPTURE / BHERO_KILL / HEROSEG_EMPTY ==="
printf "TOWN_CAPTURE=%s  BHERO_KILL=%s  HEROSEG_EMPTY=%s\n" \
  "$(grep -c 'TOWN_CAPTURE' "$LOG")" \
  "$(grep -c 'BHERO_KILL' "$LOG")" \
  "$(grep -c 'HEROSEG_EMPTY' "$LOG")"

echo "=== [GUARD] 接战次数 / 大负率 ==="
printf "GUARD=%s\n" "$(grep -c '\[GUARD\]' "$LOG")"

echo "=== 崩溃/错误 ==="
printf "err_yes=%s  SIGSEGV_OR_SIGABRT=%s\n" \
  "$(grep -c 'err=yes' "$LOG")" \
  "$(grep -cE 'SIGSEGV|SIGABRT' "$LOG")"

echo "=== [RECRUITED] / [BUILD_NEW] 经济频率 ==="
printf "RECRUITED=%s  BUILD_NEW=%s\n" \
  "$(grep -c 'RECRUITED' "$LOG")" \
  "$(grep -c 'BUILD_NEW' "$LOG")"

echo "=== 200 步截断率（近40局） ==="
grep -o 'steps=[0-9]*' "$LOG" | tail -40 | grep -o '[0-9]*' | awk '{n++; if($1==200) t++} END {if(n>0) printf "n=%d trunc200=%d ratio=%.1f%%\n", n, t, t*100/n; else print "无数据"}'
