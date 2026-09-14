#!/bin/bash
# 区分本次窗 (04:57:32 后) 与历史累积 —— WIN-1 判据①是否已开始计数
cd /mnt/d/Bigdata/hero3_fresh
LOG=train_loop.log
CUT="2026-09-15 04:57"

echo "=== 总行数 vs 本次窗行数 (>$CUT) ==="
awk -v c="$CUT" 'BEGIN{t=0;w=0} {t++; if($0 ~ c) w=1; if(w) wL++} END{printf "total=%d window=%d\n", t, wL+0}' "$LOG"

echo "=== 日志格式抽样（末 15 行） ==="
tail -15 "$LOG"

echo "=== 本次窗内 capture 相关事件 ==="
awk -v c="$CUT" 'BEGIN{w=0} $0 ~ c{w=1} w && /TOWN_CAPTURE|BHERO_KILL|HEROSEG_EMPTY|confirmed 2 frames/{print}' "$LOG" | tail -20

echo "=== 日志时间戳格式检测（含时间戳的行样例） ==="
grep -m 5 -nE '^[0-9]{4}-[0-9]{2}-[0-9]{2}|^2026-09-15' "$LOG" || echo "无 ISO 时间戳行"
