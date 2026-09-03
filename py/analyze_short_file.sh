#!/bin/bash
# 找小 (短局) hermes 文件看结束原因
echo "=== 行数 <200 的近期 hermes 文件:"
for F in $(ls -t /tmp/hermes_ep_*.log | head -8); do
  N=$(wc -l < "$F")
  if [ "$N" -lt 200 ]; then
    echo "--- $F ($N 行, $(stat -c %y "$F" | cut -d. -f1))"
    tail -8 "$F"
    echo
    break
  fi
done
