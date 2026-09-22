#!/bin/bash
set -u
OUT=/tmp/_298_evidence
echo "=== s600 结果 ==="
cat $OUT/verify_s600.txt 2>/dev/null || echo "(尚无)"
echo ""
for M in good_to_go judgement_day; do
  f=$(ls -t $OUT/ep_${M}*_s600_*.log 2>/dev/null | head -1)
  [ -z "$f" ] && continue
  echo "=== $M s600 局: $f ==="
  echo "  lines=$(wc -l < "$f")  NK2=$(grep -ac 'NK2' "$f")  SWALLOW=$(grep -ac 'EP298_SWALLOW' "$f")  EP_TIME=$(grep -ac 'EP_TIME' "$f")  fishy=$(grep -ac 'fishy' "$f")"
  echo "  尾 3 行:"
  tail -3 "$f" | cut -c1-160 | sed 's/^/    /'
  echo ""
done
ps -ef | grep traj_298 | grep -v grep | head -1 || echo "(已全部结束)"
