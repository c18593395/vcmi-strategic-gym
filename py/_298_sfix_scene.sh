#!/bin/bash
set -u
for M in good_to_go judgement_day elbow_room a_viking; do
  f=$(ls -t /tmp/_298_evidence/ep_${M}*_sfix_*.log 2>/dev/null | head -1)
  [ -z "$f" ] && continue
  echo "=== $M: $f ==="
  echo "  lines=$(wc -l < "$f")  ML-wait=$(grep -ac 'ML-wait' "$f")  SWALLOW=$(grep -ac 'EP298_SWALLOW' "$f")  timeout=$(grep -ac 'adventure_wait timed out' "$f")  fishy=$(grep -ac 'fishy' "$f")  ERROR=$(grep -ac 'ERROR' "$f")"
  echo "  尾 4 行:"
  tail -4 "$f" | cut -c1-170 | sed 's/^/    /'
  echo ""
done
