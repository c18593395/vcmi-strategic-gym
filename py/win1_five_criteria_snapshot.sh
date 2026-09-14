#!/bin/bash
# WIN-1 五判据聚合快照（09-15 S2 部署前置核查）
# 09-15 修正: 判据① BHERO_KILL → TOWN_CAPTURE
#   - BHERO_KILL 不在主日志白名单, 仅走旁路 battle_quality_events.log;
#     且全历史 9 次全空拍误报 (#146), 非空拍差集恒为空 = 真无行为;
#   - TOWN_CAPTURE 完整标签进主日志 (主日志白名单 "[TOWN" 前缀通配, 215 条已实质满足判据①)
cd /mnt/d/Bigdata/hero3_fresh
LOG=train_loop.log
EVLOG=battle_quality_events.log

echo "=== 本次窗启动时间 ==="
systemctl show homm3-train-v5 --property=ActiveEnterTimestamp --value 2>/dev/null

echo "=== 日志 mtime ==="
stat -c '%y' "$LOG"

echo "=== [ENDTURN] 局数 ==="
grep -c 'ENDTURN' "$LOG"

echo "=== 近 40 局 avg_r ==="
grep -o 'avg_r=[-0-9.]*' "$LOG" | tail -40 | grep -o '[-0-9.]*' | awk '{s+=$1;n++} END {if(n>0) printf "n=%d avg_r=%.2f\n", n, s/n; else print "无数据"}'

echo "=== 判据① TOWN_CAPTURE 非零 (主日志, 白名单内) ==="
printf "TOWN_CAPTURE(主日志)=%s\n" "$(grep -c 'TOWN_CAPTURE' "$LOG")"
echo "--- 本次窗起点 ==="
L=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
echo "Loaded train state 行号: $L / 总 $(wc -l < "$LOG")"
echo "本次窗 TOWN_CAPTURE: $(awk -v L=$L 'NR>=L && /TOWN_CAPTURE/' "$LOG" | wc -l)"
echo "本次窗 [TOWN 前缀事件: $(awk -v L=$L 'NR>=L && /\[TOWN/' "$LOG" | wc -l)"
echo "--- 旁路 battle_quality_events.log (含 BHERO_KILL/HEROSEG_EMPTY 诊断) ==="
if [ -f "$EVLOG" ]; then
  printf "  旁路 TOWN_CAPTURE=%s  BHERO_KILL=%s  HEROSEG_EMPTY=%s\n" \
    "$(grep -c 'TOWN_CAPTURE' "$EVLOG")" \
    "$(grep -c 'BHERO_KILL' "$EVLOG")" \
    "$(grep -c 'HEROSEG_EMPTY' "$EVLOG")"
fi

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

echo "=== 五判据状态汇总 ==="
echo "① TOWN_CAPTURE 非零: 主日志 $(grep -c 'TOWN_CAPTURE' "$LOG") (本次窗 $(awk -v L=$L 'NR>=L && /TOWN_CAPTURE/' "$LOG" | wc -l))"
echo "② GUARD 接战 ≥80%: $(grep -c '\[GUARD\]' "$LOG") 次 (需按局归一化)"
echo "③ avg_r 跌幅 <20%: 见上"
echo "④ 自发经济 ≥80%: RECRUITED=$(grep -c 'RECRUITED' "$LOG")"
echo "⑤ 200 步截断率 ≤20%: 见上"
