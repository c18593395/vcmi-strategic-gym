#!/bin/bash
# #298 run1 引擎日志取证 (02-27 good_to_go 327s 病态局)
set -u
OUT=/tmp/_298_evidence
echo "=== 证据目录 ==="
ls -la $OUT 2>/dev/null
echo ""
LATEST=$(ls -t $OUT/vcmi_client_good_to_go*.log 2>/dev/null | head -1)
echo "=== 取证: $LATEST ==="
echo "--- fishy 8 次的内容 ---"
grep -n "fishy" $LATEST 2>/dev/null | head -10
echo ""
echo "--- Cannot answer 上下文 (前后 2 行, 首条) ---"
ln=$(grep -n "Cannot answer the query -1" $LATEST 2>/dev/null | head -1 | cut -d: -f1)
if [ -n "${ln:-}" ]; then
  sed -n "$((ln-3)),$((ln+3))p" $LATEST
fi
echo ""
echo "--- 随机定型相关 (pickRandomObject/randomizeFaction/Random/exception) ---"
grep -inE "randomiz|pickRandom|exception|throw|error" $LATEST 2>/dev/null | grep -v "Cannot answer" | head -20
echo ""
echo "--- 时间线: 长间隔扫描 (相临行时间差 >5s 的位置) ---"
grep -oE '^\[2026-Sep-23 [0-9:.]+' $LATEST 2>/dev/null | awk -F'[:. ]' '{t=$4*3600+$5*60+$6; if(prev && t-prev>5) print "gap " t-prev "s at line " NR; prev=t}' | head -10
echo ""
echo "--- 日志总行数 + 尾 10 行 ---"
wc -l $LATEST
tail -10 $LATEST
